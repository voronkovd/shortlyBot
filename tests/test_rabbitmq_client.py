import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from analytics.rabbitmq_client import RabbitMQClient


class TestRabbitMQClient:
    
    @pytest.fixture
    def mock_pika(self):
        """Мок для pika модуля"""
        with patch('analytics.rabbitmq_client.pika') as mock_pika:
            # Мокаем соединение и канал
            mock_connection = Mock()
            mock_channel = Mock()
            mock_connection.is_closed = False
            mock_pika.BlockingConnection.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            
            yield mock_pika, mock_connection, mock_channel
    
    @pytest.fixture
    def rabbitmq_client(self, mock_pika):
        """Создает экземпляр RabbitMQClient с моками"""
        mock_pika_module, mock_connection, mock_channel = mock_pika
        
        with patch.dict('os.environ', {
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'test_user',
            'RABBITMQ_PASSWORD': 'test_pass',
            'RABBITMQ_VHOST': '/'
        }):
            client = RabbitMQClient()
            client.connection = mock_connection
            client.channel = mock_channel
            return client
    
    def test_init_connection_success(self, mock_pika):
        """Тест успешного подключения к RabbitMQ"""
        mock_pika_module, mock_connection, mock_channel = mock_pika
        
        with patch.dict('os.environ', {
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'test_user',
            'RABBITMQ_PASSWORD': 'test_pass',
            'RABBITMQ_VHOST': '/'
        }):
            client = RabbitMQClient()
            
            # Проверяем, что соединение установлено
            assert client.connection is not None
            assert client.channel is not None
            mock_pika_module.BlockingConnection.assert_called_once()
            mock_connection.channel.assert_called_once()
    
    def test_init_connection_failure(self, mock_pika):
        """Тест неудачного подключения к RabbitMQ"""
        mock_pika_module, mock_connection, mock_channel = mock_pika
        mock_pika_module.BlockingConnection.side_effect = Exception("Connection failed")
        
        with patch.dict('os.environ', {
            'RABBITMQ_HOST': 'localhost',
            'RABBITMQ_PORT': '5672',
            'RABBITMQ_USER': 'test_user',
            'RABBITMQ_PASSWORD': 'test_pass',
            'RABBITMQ_VHOST': '/'
        }):
            client = RabbitMQClient()
            
            # Проверяем, что соединение не установлено
            assert client.connection is None
            assert client.channel is None
    
    def test_declare_queues(self, rabbitmq_client):
        """Тест объявления очередей"""
        rabbitmq_client._declare_queues()
        
        # Проверяем, что все очереди объявлены (может быть больше из-за повторных вызовов)
        assert rabbitmq_client.channel.queue_declare.call_count >= 3
        
        # Проверяем параметры объявления очередей
        calls = rabbitmq_client.channel.queue_declare.call_args_list
        queue_names = [call[1]['queue'] for call in calls]
        assert 'user_stats' in queue_names
        assert 'provider_stats' in queue_names
        assert 'bot_events' in queue_names
    
    def test_send_user_stats_success(self, rabbitmq_client):
        """Тест успешной отправки статистики пользователя"""
        user_id = 12345
        username = "test_user"
        action = "download_request"
        platform = "instagram"
        success = True
        
        rabbitmq_client.send_user_stats(user_id, username, action, platform, success)
        
        # Проверяем, что сообщение отправлено
        rabbitmq_client.channel.basic_publish.assert_called_once()
        
        # Проверяем параметры отправки
        call_args = rabbitmq_client.channel.basic_publish.call_args
        assert call_args[1]['routing_key'] == 'user_stats'
        assert call_args[1]['exchange'] == ''
        
        # Проверяем содержимое сообщения
        message_body = json.loads(call_args[1]['body'])
        assert message_body['user_id'] == user_id
        assert message_body['username'] == username
        assert message_body['action'] == action
        assert message_body['platform'] == platform
        assert message_body['success'] == success
        assert 'timestamp' in message_body
    
    def test_send_user_stats_no_connection(self):
        """Тест отправки статистики без соединения"""
        client = RabbitMQClient()
        client.connection = None
        client.channel = None
        
        # Не должно вызывать исключение
        client.send_user_stats(12345, "test_user", "download_request", "instagram", True)
    
    def test_send_provider_stats_success(self, rabbitmq_client):
        """Тест успешной отправки статистики провайдера"""
        platform = "tiktok"
        action = "download_success"
        success = True
        video_size = 1024000
        processing_time = 5.5
        
        rabbitmq_client.send_provider_stats(platform, action, success, video_size, processing_time)
        
        # Проверяем, что сообщение отправлено
        rabbitmq_client.channel.basic_publish.assert_called_once()
        
        # Проверяем параметры отправки
        call_args = rabbitmq_client.channel.basic_publish.call_args
        assert call_args[1]['routing_key'] == 'provider_stats'
        
        # Проверяем содержимое сообщения
        message_body = json.loads(call_args[1]['body'])
        assert message_body['platform'] == platform
        assert message_body['action'] == action
        assert message_body['success'] == success
        assert message_body['video_size'] == video_size
        assert message_body['processing_time'] == processing_time
        assert 'timestamp' in message_body
    
    def test_send_bot_event_success(self, rabbitmq_client):
        """Тест успешной отправки события бота"""
        event_type = "bot_started"
        data = {"version": "1.0", "uptime": 3600}
        
        rabbitmq_client.send_bot_event(event_type, data)
        
        # Проверяем, что сообщение отправлено
        rabbitmq_client.channel.basic_publish.assert_called_once()
        
        # Проверяем параметры отправки
        call_args = rabbitmq_client.channel.basic_publish.call_args
        assert call_args[1]['routing_key'] == 'bot_events'
        
        # Проверяем содержимое сообщения
        message_body = json.loads(call_args[1]['body'])
        assert message_body['event_type'] == event_type
        assert message_body['data'] == data
        assert 'timestamp' in message_body
    
    def test_ensure_connection_reconnect(self, rabbitmq_client):
        """Тест переподключения при потере соединения"""
        # Симулируем закрытое соединение
        rabbitmq_client.connection.is_closed = True
        
        with patch.object(rabbitmq_client, '_connect') as mock_connect:
            rabbitmq_client._ensure_connection()
            mock_connect.assert_called_once()
    
    def test_close_connection(self, rabbitmq_client):
        """Тест закрытия соединения"""
        rabbitmq_client.close()
        rabbitmq_client.connection.close.assert_called_once()
    
    def test_close_no_connection(self):
        """Тест закрытия соединения когда его нет"""
        client = RabbitMQClient()
        client.connection = None
        
        # Не должно вызывать исключение
        client.close()
