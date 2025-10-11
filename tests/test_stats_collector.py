import pytest
from unittest.mock import Mock, patch
from analytics.stats_collector import StatsCollector


class TestStatsCollector:
    
    @pytest.fixture
    def mock_rabbitmq_client(self):
        """Мок для RabbitMQ клиента"""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def stats_collector(self, mock_rabbitmq_client):
        """Создает экземпляр StatsCollector с моком RabbitMQ"""
        with patch('analytics.stats_collector.rabbitmq_client', mock_rabbitmq_client):
            collector = StatsCollector()
            collector.rabbitmq = mock_rabbitmq_client
            return collector
    
    def test_track_user_request(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания запроса пользователя"""
        user_id = 12345
        username = "test_user"
        platform = "instagram"
        
        stats_collector.track_user_request(user_id, username, platform)
        
        # Проверяем, что метод вызван с правильными параметрами
        mock_rabbitmq_client.send_user_stats.assert_called_once_with(
            user_id=user_id,
            username=username,
            action="download_request",
            platform=platform,
            success=True
        )
    
    def test_track_user_request_no_username(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания запроса пользователя без username"""
        user_id = 12345
        username = None
        platform = "tiktok"
        
        stats_collector.track_user_request(user_id, username, platform)
        
        # Проверяем, что username заменен на "unknown"
        mock_rabbitmq_client.send_user_stats.assert_called_once_with(
            user_id=user_id,
            username="unknown",
            action="download_request",
            platform=platform,
            success=True
        )
    
    def test_track_download_success(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания успешного скачивания"""
        user_id = 12345
        username = "test_user"
        platform = "youtube"
        video_size = 2048000
        processing_time = 10.5
        
        stats_collector.track_download_success(user_id, username, platform, video_size, processing_time)
        
        # Проверяем, что отправлены оба типа статистики
        assert mock_rabbitmq_client.send_user_stats.call_count == 1
        assert mock_rabbitmq_client.send_provider_stats.call_count == 1
        
        # Проверяем параметры пользовательской статистики
        user_stats_call = mock_rabbitmq_client.send_user_stats.call_args
        assert user_stats_call[1]['user_id'] == user_id
        assert user_stats_call[1]['username'] == username
        assert user_stats_call[1]['action'] == "download_success"
        assert user_stats_call[1]['platform'] == platform
        assert user_stats_call[1]['success']
        
        # Проверяем параметры статистики провайдера
        provider_stats_call = mock_rabbitmq_client.send_provider_stats.call_args
        assert provider_stats_call[1]['platform'] == platform
        assert provider_stats_call[1]['action'] == "download_success"
        assert provider_stats_call[1]['success']
        assert provider_stats_call[1]['video_size'] == video_size
        assert provider_stats_call[1]['processing_time'] == processing_time
    
    def test_track_download_failure(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания неудачного скачивания"""
        user_id = 12345
        username = "test_user"
        platform = "rutube"
        error_message = "Video not found"
        processing_time = 5.2
        
        stats_collector.track_download_failure(user_id, username, platform, error_message, processing_time)
        
        # Проверяем, что отправлены все три типа сообщений
        assert mock_rabbitmq_client.send_user_stats.call_count == 1
        assert mock_rabbitmq_client.send_provider_stats.call_count == 1
        assert mock_rabbitmq_client.send_bot_event.call_count == 1
        
        # Проверяем параметры пользовательской статистики
        user_stats_call = mock_rabbitmq_client.send_user_stats.call_args
        assert user_stats_call[1]['action'] == "download_failed"
        assert user_stats_call[1]['success']
        
        # Проверяем параметры статистики провайдера
        provider_stats_call = mock_rabbitmq_client.send_provider_stats.call_args
        assert provider_stats_call[1]['action'] == "download_failed"
        assert provider_stats_call[1]['success']
        assert provider_stats_call[1]['processing_time'] == processing_time
        
        # Проверяем параметры события бота
        bot_event_call = mock_rabbitmq_client.send_bot_event.call_args
        assert bot_event_call[0][0] == "download_error"
        event_data = bot_event_call[0][1]
        assert event_data['user_id'] == user_id
        assert event_data['platform'] == platform
        assert event_data['error'] == error_message
        assert event_data['processing_time'] == processing_time
    
    def test_track_download_failure_no_processing_time(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания неудачного скачивания без времени обработки"""
        user_id = 12345
        username = "test_user"
        platform = "likee"
        error_message = "Connection timeout"
        
        stats_collector.track_download_failure(user_id, username, platform, error_message)
        
        # Проверяем, что processing_time передан как None
        provider_stats_call = mock_rabbitmq_client.send_provider_stats.call_args
        assert provider_stats_call[1]['processing_time'] is None
        
        bot_event_call = mock_rabbitmq_client.send_bot_event.call_args
        event_data = bot_event_call[0][1]
        assert event_data['processing_time'] is None
    
    def test_track_provider_attempt(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания попытки использования провайдера"""
        platform = "facebook"
        
        stats_collector.track_provider_attempt(platform)
        
        # Проверяем, что отправлена статистика провайдера
        mock_rabbitmq_client.send_provider_stats.assert_called_once_with(
            platform=platform,
            action="download_attempt",
            success=True
        )
    
    def test_track_bot_start(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания запуска бота"""
        with patch('analytics.stats_collector.time.time', return_value=1234567890.0):
            stats_collector.track_bot_start()
        
        # Проверяем, что отправлено событие бота
        mock_rabbitmq_client.send_bot_event.assert_called_once_with(
            "bot_started",
            {"timestamp": 1234567890.0}
        )
    
    def test_track_bot_stop(self, stats_collector, mock_rabbitmq_client):
        """Тест отслеживания остановки бота"""
        with patch('analytics.stats_collector.time.time', return_value=1234567890.0):
            stats_collector.track_bot_stop()
        
        # Проверяем, что отправлено событие бота
        mock_rabbitmq_client.send_bot_event.assert_called_once_with(
            "bot_stopped",
            {"timestamp": 1234567890.0}
        )
    
    def test_exception_handling(self, stats_collector, mock_rabbitmq_client):
        """Тест обработки исключений"""
        # Симулируем исключение в RabbitMQ клиенте
        mock_rabbitmq_client.send_user_stats.side_effect = Exception("RabbitMQ error")
        
        # Не должно вызывать исключение
        stats_collector.track_user_request(12345, "test_user", "instagram")
        
        # Проверяем, что метод был вызван
        mock_rabbitmq_client.send_user_stats.assert_called_once()
