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
    ConnectionClosedByBroker,
    StreamLostError,
)

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.vhost = os.getenv("RABBITMQ_VHOST", "/")

        self.connect_attempts = int(os.getenv("RMQ_CONNECT_ATTEMPTS", "3"))
        self.publish_retries = int(os.getenv("RMQ_PUBLISH_RETRIES", "3"))

        self._queues_args = {"x-message-ttl": 86_400_000}  # 24h


    def _params(self) -> pika.ConnectionParameters:
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=pika.PlainCredentials(self.username, self.password),
            heartbeat=0,
            blocked_connection_timeout=30,
            connection_attempts=self.connect_attempts,
            retry_delay=2,
            socket_timeout=10,
            stack_timeout=20,
            frame_max=131072,
            tcp_options={
                "TCP_KEEPIDLE": 60,
                "TCP_KEEPINTVL": 10,
                "TCP_KEEPCNT": 3,
            },
        )

    def _open(self):
        conn = pika.BlockingConnection(self._params())
        ch = conn.channel()
        try:
            ch.confirm_delivery()
        except Exception:
            pass
        ch.queue_declare(queue="user_stats", durable=True, arguments=self._queues_args)
        ch.queue_declare(
            queue="provider_stats", durable=True, arguments=self._queues_args
        )
        ch.queue_declare(queue="bot_events", durable=True, arguments=self._queues_args)
        return conn, ch

    def _publish_once(self, routing_key: str, message: Dict[str, Any]) -> None:
        conn = ch = None
        try:
            conn, ch = self._open()
            ch.basic_publish(
                exchange="",
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
        finally:
            try:
                if ch is not None:
                    pass
                if conn is not None and not getattr(conn, "is_closed", False):
                    conn.close()
            except Exception:
                pass

    def _publish_with_retries(self, routing_key: str, message: Dict[str, Any]) -> None:
        attempts = 0
        while True:
            attempts += 1
            try:
                self._publish_once(routing_key, message)
                return
            except (
                AMQPConnectionError,
                StreamLostError,
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
                if attempts >= self.publish_retries:
                    logger.error(
                        "Publish failed permanently after %s attempts", attempts
                    )
                    return
                time.sleep(min(2**attempts, 10))
            except Exception as e:
                logger.exception("Unexpected publish error: %s", e)
                return


    def _build_message(self, base: Dict[str, Any]) -> Dict[str, Any]:
        m = {"timestamp": datetime.now(timezone.utc).isoformat()}
        m.update(base)
        return m

    def send_user_stats(
        self, user_id: int, username: str, action: str, platform: str, success: bool
    ):
        try:
            self._publish_with_retries(
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
        try:
            self._publish_with_retries(
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
        except Exception as e:
            logger.error("Failed to send provider stats: %s", e)

    def send_bot_event(self, event_type: str, data: Dict[str, Any]):
        try:
            self._publish_with_retries(
                "bot_events",
                self._build_message(
                    {
                        "event_type": event_type,
                        "data": data,
                    }
                ),
            )
        except Exception as e:
            logger.error("Failed to send bot event: %s", e)

    def close(self):
        return


rabbitmq_client = RabbitMQClient()
