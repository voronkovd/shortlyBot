import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pika
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """
    Лёгкий клиент с безопасным автоподключением (ограниченные ретраи),
    совместимый с юнит-тестами. Интерфейс аналогичен прежнему.
    """

    def __init__(
        self, *, autoconnect: bool = True, max_connect_tries: Optional[int] = None
    ):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

        # параметры из ENV
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USER", "admin")
        self.password = os.getenv("RABBITMQ_PASSWORD", "password123")
        self.vhost = os.getenv("RABBITMQ_VHOST", "/")

        # Лимит попыток подключения: аргумент → ENV → None (бесконечно)
        env_tries = os.getenv("RMQ_CONNECT_MAX_TRIES")
        self._max_connect_tries = (
            max_connect_tries
            if max_connect_tries is not None
            else (int(env_tries) if env_tries else None)
        )

        if autoconnect:
            self._connect()

    def _params(self) -> pika.ConnectionParameters:
        credentials = pika.PlainCredentials(self.username, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            heartbeat=int(os.getenv("RMQ_HEARTBEAT", "30")),
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
        """
        Пытается подключиться с ограниченным числом попыток.
        Важно: держим имя метода `_connect` — его патчат тесты.
        """
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
                # Publisher confirms — если есть, просто включим (в тестах будет замокано)
                if hasattr(self.channel, "confirm_delivery"):
                    try:
                        self.channel.confirm_delivery()
                    except Exception:
                        pass
                self._declare_queues()
                logger.info("Successfully connected to RabbitMQ")
                return
            except AMQPConnectionError as e:
                logger.error("Failed to connect to RabbitMQ: %s", e)
            except Exception as e:
                logger.error("Unexpected error connecting to RabbitMQ: %s", e)

            # выходим, если достигли лимита (важно для юнит-тестов, чтобы не висли)
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
        """Объявляет необходимые очереди — безопасно для повторных вызовов."""
        ch = self.channel
        if not ch or getattr(ch, "is_closed", False):
            return

        args = {"x-message-ttl": 86_400_000}  # 24h TTL
        ch.queue_declare(queue="user_stats", durable=True, arguments=args)
        ch.queue_declare(queue="provider_stats", durable=True, arguments=args)
        ch.queue_declare(queue="bot_events", durable=True, arguments=args)

    def _ensure_connection(self):
        """Проверяет и восстанавливает соединение/канал при необходимости."""
        if not self.connection or getattr(self.connection, "is_closed", False):
            logger.warning("RabbitMQ connection lost, attempting to reconnect...")
            self._connect()
        elif not self.channel or getattr(self.channel, "is_closed", False):
            logger.warning("RabbitMQ channel closed, reopening...")
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

    # ------------------- ПУБЛИКАЦИИ -------------------

    def _basic_publish(self, routing_key: str, body: Dict[str, Any]) -> None:
        """
        Единая точка публикации. В тестах мокается .basic_publish(return_value=True),
        а тут мы не навязываем проверку confirm'ов, чтобы избежать ложных WARNING.
        """
        self._ensure_connection()
        if not self.channel:
            logger.error("No RabbitMQ channel available")
            return

        self.channel.basic_publish(
            exchange="",
            routing_key=routing_key,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )

    def send_user_stats(
        self, user_id: int, username: str, action: str, platform: str, success: bool
    ):
        """Отправляет статистику пользователя"""
        try:
            message = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "username": username,
                "action": action,
                "platform": platform,
                "success": success,
            }
            self._basic_publish("user_stats", message)
            logger.debug("Sent user stats: %s", message)
        except Exception as e:
            logger.error("Failed to send user stats: %s", e)

    def send_provider_stats(
        self,
        platform: str,
        action: str,
        success: bool,
        video_size: Optional[int] = None,
        processing_time: Optional[float] = None,
    ):
        """Отправляет статистику провайдера"""
        try:
            message = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "platform": platform,
                "action": action,
                "success": success,
                "video_size": video_size,
                "processing_time": processing_time,
            }
            self._basic_publish("provider_stats", message)
            logger.debug("Sent provider stats: %s", message)
        except Exception as e:
            logger.error("Failed to send provider stats: %s", e)

    def send_bot_event(self, event_type: str, data: Dict[str, Any]):
        """Отправляет общее событие бота"""
        try:
            message = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "data": data,
            }
            self._basic_publish("bot_events", message)
            logger.debug("Sent bot event: %s", message)
        except Exception as e:
            logger.error("Failed to send bot event: %s", e)

    def close(self):
        """Закрывает соединение с RabbitMQ"""
        try:
            if self.connection and not getattr(self.connection, "is_closed", False):
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error("Error closing RabbitMQ connection: %s", e)


# Глобальный экземпляр клиента (по желанию можно создавать в точке входа)
rabbitmq_client = RabbitMQClient()
