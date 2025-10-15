import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pika
from pika.exceptions import (
    AMQPConnectionError,
    ChannelClosedByBroker,
    StreamLostError,
    ConnectionClosedByBroker,
)

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

        # env
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USER", "admin")
        self.password = os.getenv("RABBITMQ_PASSWORD", "password123")
        self.vhost = os.getenv("RABBITMQ_VHOST", "/")

        # публикации повторяем до N раз
        self.max_publish_retries = int(os.getenv("RMQ_PUBLISH_RETRIES", "5"))

        self._connect_with_retries()

    def _params(self) -> pika.ConnectionParameters:
        credentials = pika.PlainCredentials(self.username, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            heartbeat=int(os.getenv("RMQ_HEARTBEAT", "30")),        # короче — надёжнее через NAT
            blocked_connection_timeout=300,
            connection_attempts=10,
            retry_delay=5,
            socket_timeout=10,
            stack_timeout=30,
            frame_max=131072,  # 128 KiB
            tcp_options={
                "TCP_KEEPIDLE": 60,
                "TCP_KEEPINTVL": 10,
                "TCP_KEEPCNT": 3,
            },
        )

    def _connect_with_retries(self):
        backoff = 1.0
        while True:
            try:
                logger.info("Connecting to RabbitMQ %s:%s vhost=%s", self.host, self.port, self.vhost)
                self.connection = pika.BlockingConnection(self._params())
                self.channel = self.connection.channel()
                # включаем publisher confirms один раз на канал
                self.channel.confirm_delivery()
                self._declare_queues()
                logger.info("Successfully connected to RabbitMQ")
                return
            except AMQPConnectionError as e:
                logger.error("Failed to connect to RabbitMQ: %s", e)
            except Exception as e:
                logger.error("Unexpected error connecting to RabbitMQ: %s", e)

            time.sleep(min(backoff, 15))
            backoff *= 2

    def _declare_queues(self):
        if not self.channel or self.channel.is_closed:
            return
        args = {"x-message-ttl": 86_400_000}  # 24h TTL
        self.channel.queue_declare(queue="user_stats", durable=True, arguments=args)
        self.channel.queue_declare(queue="provider_stats", durable=True, arguments=args)
        self.channel.queue_declare(queue="bot_events", durable=True, arguments=args)

    def _ensure_channel(self):
        """Проверяем/восстанавливаем соединение и канал."""
        if not self.connection or self.connection.is_closed:
            logger.warning("RabbitMQ connection lost, reconnecting...")
            self._connect_with_retries()
        elif not self.channel or self.channel.is_closed:
            logger.warning("RabbitMQ channel closed, reopening...")
            try:
                self.channel = self.connection.channel()
                self.channel.confirm_delivery()
                self._declare_queues()
            except Exception:
                # если не получилось — переподключаем всё
                self._connect_with_retries()

    # --- унифицированная публикация с ретраями и реконнектом ---
    def _publish(self, routing_key: str, message: Dict[str, Any]) -> bool:
        payload = json.dumps(message, ensure_ascii=False)
        attempt = 0
        while True:
            self._ensure_channel()
            try:
                ok = self.channel.basic_publish(
                    exchange="",  # default exchange → прямой роутинг в очередь
                    routing_key=routing_key,
                    body=payload,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # persistent
                        content_type="application/json",
                    ),
                    mandatory=False,
                )
                if ok is True:
                    return True
                # confirm_delivery должен вернуть True, но на всякий…
                raise StreamLostError("Publish not confirmed")
            except (
                StreamLostError,
                AMQPConnectionError,
                ConnectionClosedByBroker,
                ChannelClosedByBroker,
                ConnectionResetError,
            ) as e:
                attempt += 1
                logger.warning(
                    "Publish failed (attempt %d/%d): %s",
                    attempt, self.max_publish_retries, e,
                )
                # полная реконнекция перед повтором
                try:
                    if self.connection and not self.connection.is_closed:
                        self.connection.close()
                except Exception:
                    pass
                self.connection = None
                self.channel = None

                if attempt >= self.max_publish_retries:
                    logger.error("Publish failed permanently after %d attempts", attempt)
                    return False

                time.sleep(min(2 ** attempt, 15))
            except Exception as e:
                logger.exception("Unexpected publish error: %s", e)
                return False

    # --- публичные методы ---
    def send_user_stats(self, user_id: int, username: str, action: str, platform: str, success: bool):
        msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "username": username,
            "action": action,
            "platform": platform,
            "success": success,
        }
        if self._publish("user_stats", msg):
            logger.debug("Sent user stats: %s", msg)
        else:
            logger.error("Failed to send user stats after retries")

    def send_provider_stats(
        self,
        platform: str,
        action: str,
        success: bool,
        video_size: Optional[int] = None,
        processing_time: Optional[float] = None,
    ):
        msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": platform,
            "action": action,
            "success": success,
            "video_size": video_size,
            "processing_time": processing_time,
        }
        if self._publish("provider_stats", msg):
            logger.debug("Sent provider stats: %s", msg)
        else:
            logger.error("Failed to send provider stats after retries")

    def send_bot_event(self, event_type: str, data: Dict[str, Any]):
        msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data,
        }
        if self._publish("bot_events", msg):
            logger.debug("Sent bot event: %s", msg)
        else:
            logger.error("Failed to send bot event after retries")

    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error("Error closing RabbitMQ connection: %s", e)


# Глобальный экземпляр (лучше создавать в точке входа приложения)
rabbitmq_client = RabbitMQClient()
