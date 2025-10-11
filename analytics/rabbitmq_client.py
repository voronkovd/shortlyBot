import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._connect()
    
    def _connect(self):
        """Устанавливает соединение с RabbitMQ"""
        try:
            # Получаем настройки из переменных окружения
            host = os.getenv('RABBITMQ_HOST', 'localhost')
            port = int(os.getenv('RABBITMQ_PORT', '5672'))
            username = os.getenv('RABBITMQ_USER', 'admin')
            password = os.getenv('RABBITMQ_PASSWORD', 'password123')
            vhost = os.getenv('RABBITMQ_VHOST', '/')
            
            # Создаем параметры подключения
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=vhost,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            # Устанавливаем соединение
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Объявляем очереди
            self._declare_queues()
            
            logger.info("Successfully connected to RabbitMQ")
            
        except AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to RabbitMQ: {e}")
            self.connection = None
            self.channel = None
    
    def _declare_queues(self):
        """Объявляет необходимые очереди"""
        if not self.channel:
            return
            
        # Очередь для статистики пользователей
        self.channel.queue_declare(
            queue='user_stats',
            durable=True,  # Очередь переживет перезапуск RabbitMQ
            arguments={'x-message-ttl': 86400000}  # TTL 24 часа
        )
        
        # Очередь для статистики провайдеров
        self.channel.queue_declare(
            queue='provider_stats',
            durable=True,
            arguments={'x-message-ttl': 86400000}
        )
        
        # Очередь для общих событий
        self.channel.queue_declare(
            queue='bot_events',
            durable=True,
            arguments={'x-message-ttl': 86400000}
        )
    
    def _ensure_connection(self):
        """Проверяет и восстанавливает соединение при необходимости"""
        if not self.connection or self.connection.is_closed:
            logger.warning("RabbitMQ connection lost, attempting to reconnect...")
            self._connect()
    
    def send_user_stats(self, user_id: int, username: str, action: str, platform: str, success: bool):
        """Отправляет статистику пользователя"""
        try:
            self._ensure_connection()
            if not self.channel:
                logger.error("No RabbitMQ channel available")
                return
            
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'username': username,
                'action': action,  # 'download_request', 'download_success', 'download_failed'
                'platform': platform,
                'success': success
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='user_stats',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Делаем сообщение персистентным
                    content_type='application/json'
                )
            )
            
            logger.debug(f"Sent user stats: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send user stats: {e}")
    
    def send_provider_stats(self, platform: str, action: str, success: bool, 
                           video_size: Optional[int] = None, processing_time: Optional[float] = None):
        """Отправляет статистику провайдера"""
        try:
            self._ensure_connection()
            if not self.channel:
                logger.error("No RabbitMQ channel available")
                return
            
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'platform': platform,
                'action': action,  # 'download_attempt', 'download_success', 'download_failed'
                'success': success,
                'video_size': video_size,
                'processing_time': processing_time
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='provider_stats',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.debug(f"Sent provider stats: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send provider stats: {e}")
    
    def send_bot_event(self, event_type: str, data: Dict[str, Any]):
        """Отправляет общее событие бота"""
        try:
            self._ensure_connection()
            if not self.channel:
                logger.error("No RabbitMQ channel available")
                return
            
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'data': data
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='bot_events',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.debug(f"Sent bot event: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send bot event: {e}")
    
    def close(self):
        """Закрывает соединение с RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Глобальный экземпляр клиента
rabbitmq_client = RabbitMQClient()
