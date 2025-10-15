import json
from unittest.mock import Mock, patch

import pytest

from analytics.rabbitmq_client import AMQPConnectionError, RabbitMQClient


class TestRabbitMQClient:
    @pytest.fixture
    def mock_pika(self):
        with patch("analytics.rabbitmq_client.pika") as mp:
            conn = Mock()
            ch = Mock()

            conn.is_closed = False
            conn.channel.return_value = ch

            ch.basic_publish = Mock(return_value=True)
            ch.queue_declare = Mock()
            ch.confirm_delivery = Mock(return_value=None)

            mp.BlockingConnection.return_value = conn

            yield mp, conn, ch

    @pytest.fixture
    def rabbitmq_client(self):
        return RabbitMQClient()

    def _assert_three_queues_declared(self, ch):
        calls = ch.queue_declare.call_args_list
        queues = [c.kwargs["queue"] for c in calls]
        assert "user_stats" in queues
        assert "provider_stats" in queues
        assert "bot_events" in queues

    def test_send_user_stats_success(self, mock_pika, rabbitmq_client):
        mp, conn, ch = mock_pika

        rabbitmq_client.send_user_stats(
            user_id=12345,
            username="test_user",
            action="download_request",
            platform="instagram",
            success=True,
        )

        mp.BlockingConnection.assert_called_once()
        conn.channel.assert_called_once()

        self._assert_three_queues_declared(ch)

        ch.basic_publish.assert_called_once()
        args, kwargs = ch.basic_publish.call_args
        assert kwargs["exchange"] == ""
        assert kwargs["routing_key"] == "user_stats"

        body = json.loads(kwargs["body"])
        assert body["user_id"] == 12345
        assert body["username"] == "test_user"
        assert body["action"] == "download_request"
        assert body["platform"] == "instagram"
        assert body["success"] is True
        assert "timestamp" in body

        conn.close.assert_called_once()

    def test_send_provider_stats_success(self, mock_pika, rabbitmq_client):
        mp, conn, ch = mock_pika

        rabbitmq_client.send_provider_stats(
            platform="tiktok",
            action="download_success",
            success=True,
            video_size=1024,
            processing_time=5.5,
        )

        mp.BlockingConnection.assert_called_once()
        conn.channel.assert_called_once()
        self._assert_three_queues_declared(ch)

        ch.basic_publish.assert_called_once()
        body = json.loads(ch.basic_publish.call_args.kwargs["body"])
        assert body["platform"] == "tiktok"
        assert body["action"] == "download_success"
        assert body["success"] is True
        assert body["video_size"] == 1024
        assert body["processing_time"] == 5.5
        assert "timestamp" in body

        conn.close.assert_called_once()

    def test_send_bot_event_success(self, mock_pika, rabbitmq_client):
        mp, conn, ch = mock_pika

        rabbitmq_client.send_bot_event(
            "bot_started", {"version": "1.0", "uptime": 3600}
        )

        mp.BlockingConnection.assert_called_once()
        conn.channel.assert_called_once()
        self._assert_three_queues_declared(ch)

        ch.basic_publish.assert_called_once()
        kwargs = ch.basic_publish.call_args.kwargs
        assert kwargs["routing_key"] == "bot_events"

        body = json.loads(kwargs["body"])
        assert body["event_type"] == "bot_started"
        assert body["data"] == {"version": "1.0", "uptime": 3600}
        assert "timestamp" in body

        conn.close.assert_called_once()

    def test_queue_declare_each_send(self, mock_pika, rabbitmq_client):
        mp, conn, ch = mock_pika

        rabbitmq_client.send_user_stats(1, "u", "a", "p", True)
        rabbitmq_client.send_provider_stats("p", "a", True, 1, 0.1)

        assert mp.BlockingConnection.call_count == 2
        assert conn.channel.call_count == 2

        assert ch.queue_declare.call_count == 6
        self._assert_three_queues_declared(ch)

        assert ch.basic_publish.call_count == 2
        assert conn.close.call_count == 2

    def test_connection_error_retries(self, mock_pika, rabbitmq_client, monkeypatch):
        mp, conn, ch = mock_pika
        mp.BlockingConnection.side_effect = AMQPConnectionError("down")

        monkeypatch.setenv("RMQ_PUBLISH_RETRIES", "3")

        rabbitmq_client.send_user_stats(1, "u", "a", "p", True)

        assert mp.BlockingConnection.call_count == 3
        assert not conn.channel.called
        assert not ch.basic_publish.called

    def test_close_noop(self, rabbitmq_client):
        rabbitmq_client.close()
