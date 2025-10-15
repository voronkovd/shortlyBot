import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Any, Dict, Optional, Tuple

import pika
from pika.exceptions import (
    AMQPConnectionError,
    ChannelClosedByBroker,
    ConnectionClosedByBroker,
    StreamLostError,
)

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """
    Клиент RabbitMQ с двумя режимами:
      - синхронный (по умолчанию для тестов) — как раньше;
      - потоковый (RMQ_THREADED=1) — вся работа с pika в отдельном потоке,
        который крутит process_data_events() и отправляет heartbeats.
    """

    def __init__(
        self, *, autoconnect: bool = True, max_connect_tries: Optional[int] = None
    ):
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USER", "admin")
        self.password = os.getenv("RABBITMQ_PASSWORD", "password123")
        self.vhost = os.getenv("RABBITMQ_VHOST", "/")

        self.heartbeat = int(os.getenv("RMQ_HEARTBEAT", "120"))  # увеличили дефолт
        self.publish_retries = int(os.getenv("RMQ_PUBLISH_RETRIES", "5"))
        self.threaded = os.getenv("RMQ_THREADED", "0") == "1"

        # лимит попыток подключения: для тестов можно задать RMQ_CONNECT_MAX_TRIES
        env_tries = os.getenv("RMQ_CONNECT_MAX_TRIES")
        self._max_connect_tries = (
            max_connect_tries
            if max_connect_tries is not None
            else (int(env_tries) if env_tries else None)
        )

        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

        # Для потокового режима
        self._pub_queue: "Queue[Tuple[str, Dict[str, Any]]]" = Queue()
        self._th: Optional[threading.Thread] = None
        self._stop = threading.Event()

        if autoconnect:
            if self.threaded:
                self._start_thread()
            else:
                self._connect()

    # -------------------- внутренности --------------------

    def _params(self) -> pika.ConnectionParameters:
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=pika.PlainCredentials(self.username, self.password),
            heartbeat=self.heartbeat,
            blocked_connection_timeout=300,
            connection_attempts=3,
            retry_delay=2,
            socket_timeout=10,
            stack_timeout=30,
            frame_max=131072,
            tcp_options={
                "TCP_KEEPIDLE": 60,
                "TCP_KEEPINTVL": 10,
                "TCP_KEEPCNT": 3,
            },
        )

    def _connect(self):
        backoff = 1.0
        attempts = 0
        while True:
            attempts += 1
            try:
                logger.info(
                    "Connecting to RabbitMQ %s:%s vhost=%s",
                    self.host,
                    self.port,
                    self.vhost,
                )
                self.connection = pika.BlockingConnection(self._params())
                self.channel = self.connection.channel()
                if hasattr(self.channel, "confirm_delivery"):
                    try:
                        self.channel.confirm_delivery()
                    except Exception:
                        pass
                self._declare_queues()
                logger.info("Successfully connected to RabbitMQ")
                return
            except Exception as e:
                logger.error("Connect failed: %s", e)
                if (
                    self._max_connect_tries is not None
                    and attempts >= self._max_connect_tries
                ):
                    self.connection = None
                    self.channel = None
                    return
                time.sleep(min(backoff, 5))
                backoff *= 2

    def _declare_queues(self):
        ch = self.channel
        if not ch or getattr(ch, "is_closed", False):
            return
        args = {"x-message-ttl": 86_400_000}
        ch.queue_declare(queue="user_stats", durable=True, arguments=args)
        ch.queue_declare(queue="provider_stats", durable=True, arguments=args)
        ch.queue_declare(queue="bot_events", durable=True, arguments=args)

    def _ensure_connection(self):
        if not self.connection or getattr(self.connection, "is_closed", False):
            self._connect()
        elif not self.channel or getattr(self.channel, "is_closed", False):
            try:
                self.channel = self.connection.channel()
                if hasattr(self.channel, "confirm_delivery"):
                    try:
                        self.channel.confirm_delivery()
                    except Exception:
                        pass
                self._declare_queues()
            except Exception:
                self._connect()

    # -------------------- публикация (синхронный режим) --------------------

    def _basic_publish_sync(self, routing_key: str, body: Dict[str, Any]) -> None:
        payload = json.dumps(body)
        attempts = 0
        while True:
            attempts += 1
            self._ensure_connection()
            if not self.channel:
                logger.error("No RabbitMQ channel available")
                return
            try:
                self.channel.basic_publish(
                    exchange="",
                    routing_key=routing_key,
                    body=payload,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type="application/json",
                    ),
                )
                return
            except (
                StreamLostError,
                AMQPConnectionError,
                ConnectionClosedByBroker,
                ChannelClosedByBroker,
                ConnectionResetError,
            ) as e:
                logger.warning(
                    "Publish failed (attempt %s/%s): %s",
                    attempts,
                    self.publish_retries,
                    e,
                )
                try:
                    if self.connection and not getattr(
                        self.connection, "is_closed", False
                    ):
                        self.connection.close()
                except Exception:
                    pass
                self.connection = None
                self.channel = None
                if attempts >= self.publish_retries:
                    logger.error(
                        "Publish failed permanently after %s attempts", attempts
                    )
                    return
                time.sleep(min(2**attempts, 15))
            except Exception as e:
                logger.exception("Unexpected publish error: %s", e)
                return

    # -------------------- потоковый режим --------------------

    def _start_thread(self):
        if self._th and self._th.is_alive():
            return
        self._stop.clear()
        self._th = threading.Thread(
            target=self._run_thread, name="RMQPublisher", daemon=True
        )
        self._th.start()

    def _run_thread(self):
        """Весь I/O pika живёт здесь: соединение, heartbeats, публикации."""
        backoff = 1.0
        while not self._stop.is_set():
            try:
                # подключаемся
                self._connect()
                if not self.connection or not self.channel:
                    # не удалось — подождём и повторим
                    time.sleep(min(backoff, 5))
                    backoff = min(backoff * 2, 15)
                    continue

                backoff = 1.0  # сбросили бэкоф после успешного коннекта

                while not self._stop.is_set():
                    # 1) публикуем всё, что накопилось
                    try:
                        routing_key, body = self._pub_queue.get(timeout=0.5)
                        try:
                            self.channel.basic_publish(
                                exchange="",
                                routing_key=routing_key,
                                body=json.dumps(body),
                                properties=pika.BasicProperties(
                                    delivery_mode=2,
                                    content_type="application/json",
                                ),
                            )
                        finally:
                            self._pub_queue.task_done()
                    except Empty:
                        pass

                    # 2) крутим I/O, чтобы отправлять heartbeat’ы
                    try:
                        # time_limit чуть меньше heartbeat/2
                        tl = max(min(self.heartbeat // 2, 10), 1)
                        self.connection.process_data_events(time_limit=tl)
                        time.sleep(0.2)
                    except Exception:
                        # пусть отработает общий reconnect снаружи
                        raise

            except (
                StreamLostError,
                AMQPConnectionError,
                ConnectionClosedByBroker,
                ChannelClosedByBroker,
                ConnectionResetError,
            ) as e:
                logger.warning("RMQ thread: connection lost: %s — reconnecting…", e)
                self._safe_close()
                self.connection = None
                self.channel = None
                time.sleep(1.0)
            except Exception as e:
                logger.exception("RMQ thread: unexpected error: %s", e)
                self._safe_close()
                self.connection = None
                self.channel = None
                time.sleep(1.0)

        self._safe_close()
        self.connection = None
        self.channel = None

    def _safe_close(self):
        try:
            if self.connection and not getattr(self.connection, "is_closed", False):
                self.connection.close()
        except Exception:
            pass

    # -------------------- публичные методы --------------------

    def _build_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        m = {"timestamp": datetime.now(timezone.utc).isoformat()}
        m.update(payload)
        return m

    def _publish(self, routing_key: str, message: Dict[str, Any]) -> None:
        if self.threaded:
            # отдаём в очередь потоку-паблишеру
            self._pub_queue.put((routing_key, message))
        else:
            self._basic_publish_sync(routing_key, message)

    def send_user_stats(
        self, user_id: int, username: str, action: str, platform: str, success: bool
    ):
        self._publish(
            "user_stats",
            self._build_message(
                {
                    "user_id": user_id,
                    "username": username,
                    "action": action,
                    "platform": platform,
                    "success": success,
                }
            ),
        )

    def send_provider_stats(
        self,
        platform: str,
        action: str,
        success: bool,
        video_size: Optional[int] = None,
        processing_time: Optional[float] = None,
    ):
        self._publish(
            "provider_stats",
            self._build_message(
                {
                    "platform": platform,
                    "action": action,
                    "success": success,
                    "video_size": video_size,
                    "processing_time": processing_time,
                }
            ),
        )

    def send_bot_event(self, event_type: str, data: Dict[str, Any]):
        self._publish(
            "bot_events",
            self._build_message(
                {
                    "event_type": event_type,
                    "data": data,
                }
            ),
        )

    def close(self):
        if self.threaded:
            self._stop.set()
            if self._th and self._th.is_alive():
                self._th.join(timeout=5)
        self._safe_close()


# Глобальный экземпляр (по желанию)
rabbitmq_client = RabbitMQClient()
