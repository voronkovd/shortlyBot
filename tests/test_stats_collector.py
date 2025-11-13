from unittest.mock import Mock, patch

import pytest

from analytics.stats_collector import StatsCollector


class TestStatsCollector:

    @pytest.fixture
    def mock_rabbitmq_client(self):
        mock_client = Mock()
        return mock_client

    @pytest.fixture
    def stats_collector(self, mock_rabbitmq_client):
        with patch("analytics.stats_collector.rabbitmq_client", mock_rabbitmq_client):
            collector = StatsCollector()
            collector.rabbitmq = mock_rabbitmq_client
            return collector

    def test_track_user_request(self, stats_collector, mock_rabbitmq_client):
        user_id = 12345
        username = "test_user"
        platform = "instagram"

        stats_collector.track_user_request(user_id, username, platform)

        mock_rabbitmq_client.send_user_stats.assert_called_once_with(
            user_id=user_id,
            username=username,
            action="download_request",
            platform=platform,
            success=True,
        )

    def test_track_user_request_no_username(
        self, stats_collector, mock_rabbitmq_client
    ):
        user_id = 12345
        username = None
        platform = "tiktok"

        stats_collector.track_user_request(user_id, username, platform)

        mock_rabbitmq_client.send_user_stats.assert_called_once_with(
            user_id=user_id,
            username="user_12345",
            action="download_request",
            platform=platform,
            success=True,
        )

    def test_track_download_success(self, stats_collector, mock_rabbitmq_client):
        user_id = 12345
        username = "test_user"
        platform = "youtube"
        video_size = 2048000
        processing_time = 10.5

        stats_collector.track_download_success(
            user_id, username, platform, video_size, processing_time
        )

        assert mock_rabbitmq_client.send_user_stats.call_count == 1
        assert mock_rabbitmq_client.send_provider_stats.call_count == 1

        user_stats_call = mock_rabbitmq_client.send_user_stats.call_args
        assert user_stats_call[1]["user_id"] == user_id
        assert user_stats_call[1]["username"] == username
        assert user_stats_call[1]["action"] == "download_success"
        assert user_stats_call[1]["platform"] == platform
        assert user_stats_call[1]["success"]

        provider_stats_call = mock_rabbitmq_client.send_provider_stats.call_args
        assert provider_stats_call[1]["platform"] == platform
        assert provider_stats_call[1]["action"] == "download_success"
        assert provider_stats_call[1]["success"]
        assert provider_stats_call[1]["video_size"] == video_size
        assert provider_stats_call[1]["processing_time"] == processing_time

    def test_track_download_failure(self, stats_collector, mock_rabbitmq_client):
        user_id = 12345
        username = "test_user"
        platform = "rutube"
        error_message = "Video not found"
        processing_time = 5.2

        stats_collector.track_download_failure(
            user_id, username, platform, error_message, processing_time
        )

        assert mock_rabbitmq_client.send_user_stats.call_count == 1
        assert mock_rabbitmq_client.send_provider_stats.call_count == 1
        assert mock_rabbitmq_client.send_bot_event.call_count == 1

        user_stats_call = mock_rabbitmq_client.send_user_stats.call_args
        assert user_stats_call[1]["action"] == "download_failed"
        assert not user_stats_call[1]["success"]

        provider_stats_call = mock_rabbitmq_client.send_provider_stats.call_args
        assert provider_stats_call[1]["action"] == "download_failed"
        assert not provider_stats_call[1]["success"]
        assert provider_stats_call[1]["processing_time"] == processing_time

        bot_event_call = mock_rabbitmq_client.send_bot_event.call_args
        assert bot_event_call[0][0] == "download_error"
        event_data = bot_event_call[0][1]
        assert event_data["user_id"] == user_id
        assert event_data["platform"] == platform
        assert event_data["error"] == error_message
        assert event_data["processing_time"] == processing_time

    def test_track_download_failure_no_processing_time(
        self, stats_collector, mock_rabbitmq_client
    ):
        user_id = 12345
        username = "test_user"
        platform = "likee"
        error_message = "Connection timeout"

        stats_collector.track_download_failure(
            user_id, username, platform, error_message
        )

        provider_stats_call = mock_rabbitmq_client.send_provider_stats.call_args
        assert provider_stats_call[1]["processing_time"] is None

        bot_event_call = mock_rabbitmq_client.send_bot_event.call_args
        event_data = bot_event_call[0][1]
        assert event_data["processing_time"] is None

    def test_track_provider_attempt(self, stats_collector, mock_rabbitmq_client):
        platform = "facebook"

        stats_collector.track_provider_attempt(platform)

        mock_rabbitmq_client.send_provider_stats.assert_called_once_with(
            platform=platform, action="download_attempt", success=True
        )

    def test_track_bot_start(self, stats_collector, mock_rabbitmq_client):
        with patch("analytics.stats_collector.time.time", return_value=1234567890.0):
            stats_collector.track_bot_start()

        mock_rabbitmq_client.send_bot_event.assert_called_once_with(
            "bot_started", {"timestamp": 1234567890.0}
        )

    def test_track_bot_stop(self, stats_collector, mock_rabbitmq_client):
        with patch("analytics.stats_collector.time.time", return_value=1234567890.0):
            stats_collector.track_bot_stop()

        mock_rabbitmq_client.send_bot_event.assert_called_once_with(
            "bot_stopped", {"timestamp": 1234567890.0}
        )

    def test_exception_handling(self, stats_collector, mock_rabbitmq_client):
        mock_rabbitmq_client.send_user_stats.side_effect = Exception("RabbitMQ error")

        stats_collector.track_user_request(12345, "test_user", "instagram")

        mock_rabbitmq_client.send_user_stats.assert_called_once()

    def test_get_display_username_with_username(self, stats_collector):
        """Тест получения отображаемого username когда username есть"""
        result = stats_collector._get_display_username(12345, "test_user")
        assert result == "test_user"

    def test_get_display_username_without_username(self, stats_collector):
        """Тест получения отображаемого username когда username отсутствует"""
        result = stats_collector._get_display_username(12345, None)
        assert result == "user_12345"

    def test_get_display_username_empty_username(self, stats_collector):
        """Тест получения отображаемого username когда username пустой"""
        result = stats_collector._get_display_username(12345, "")
        assert result == "user_12345"

    def test_track_download_failure_unknown_platform(
        self, stats_collector, mock_rabbitmq_client
    ):
        """Тест что ошибки для неизвестных платформ игнорируются"""
        user_id = 12345
        username = "test_user"
        platform = "unknown"
        error_message = "Some error"
        processing_time = 5.2

        stats_collector.track_download_failure(
            user_id, username, platform, error_message, processing_time
        )

        # Не должно быть вызовов для неизвестной платформы
        mock_rabbitmq_client.send_user_stats.assert_not_called()
        mock_rabbitmq_client.send_provider_stats.assert_not_called()
        mock_rabbitmq_client.send_bot_event.assert_not_called()

    def test_track_download_failure_known_platforms(
        self, stats_collector, mock_rabbitmq_client
    ):
        """Тест что ошибки для всех известных платформ отслеживаются"""
        known_platforms = [
            "instagram",
            "tiktok",
            "youtube",
            "likee",
            "facebook",
            "rutube",
        ]

        for platform in known_platforms:
            mock_rabbitmq_client.reset_mock()
            stats_collector.track_download_failure(
                12345, "test_user", platform, "Test error", 1.0
            )

            # Для каждой известной платформы должны быть вызовы
            assert mock_rabbitmq_client.send_user_stats.call_count == 1
            assert mock_rabbitmq_client.send_provider_stats.call_count == 1
            assert mock_rabbitmq_client.send_bot_event.call_count == 1
