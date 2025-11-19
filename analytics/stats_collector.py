import logging
import time
from typing import Optional

from .rabbitmq_client import rabbitmq_client

logger = logging.getLogger(__name__)


class StatsCollector:

    # Список известных платформ, для которых мы отслеживаем ошибки
    KNOWN_PLATFORMS = {
        "instagram",
        "tiktok",
        "youtube",
        "likee",
        "facebook",
        "rutube",
        "reddit",
    }

    def __init__(self):
        self.rabbitmq = rabbitmq_client

    def _should_track_platform(self, platform: str) -> bool:
        if platform in self.KNOWN_PLATFORMS:
            return True
        logger.debug(f"Skipping stats for unknown platform: {platform}")
        return False

    def _get_display_username(self, user_id: int, username: str) -> str:
        """Создает более информативный username для отображения"""
        if username:
            return username
        return f"user_{user_id}"

    def track_user_request(self, user_id: int, username: str, platform: str):
        if not self._should_track_platform(platform):
            return
        try:
            # Создаем более информативный username
            display_username = self._get_display_username(user_id, username)

            self.rabbitmq.send_user_stats(
                user_id=user_id,
                username=display_username,
                action="download_request",
                platform=platform,
                success=True,
            )
            logger.info(f"Tracked user request: {user_id} for {platform}")
        except Exception as e:
            logger.error(f"Failed to track user request: {e}")

    def track_download_success(
        self,
        user_id: int,
        username: str,
        platform: str,
        video_size: int,
        processing_time: float,
    ):
        if not self._should_track_platform(platform):
            return
        try:
            # Создаем более информативный username
            display_username = self._get_display_username(user_id, username)

            # Статистика пользователя
            self.rabbitmq.send_user_stats(
                user_id=user_id,
                username=display_username,
                action="download_success",
                platform=platform,
                success=True,
            )

            # Статистика провайдера
            self.rabbitmq.send_provider_stats(
                platform=platform,
                action="download_success",
                success=True,
                video_size=video_size,
                processing_time=processing_time,
            )

            logger.info(
                f"Tracked successful download: {user_id} from {platform}, size: {video_size} bytes, time: {processing_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"Failed to track download success: {e}")

    def track_download_failure(
        self,
        user_id: int,
        username: str,
        platform: str,
        error_message: str,
        processing_time: Optional[float] = None,
    ):
        # Игнорируем ошибки для неизвестных платформ
        if not self._should_track_platform(platform):
            return

        try:
            # Создаем более информативный username
            display_username = self._get_display_username(user_id, username)

            self.rabbitmq.send_user_stats(
                user_id=user_id,
                username=display_username,
                action="download_failed",
                platform=platform,
                success=False,
            )

            self.rabbitmq.send_provider_stats(
                platform=platform,
                action="download_failed",
                success=False,
                processing_time=processing_time,
            )

            self.rabbitmq.send_bot_event(
                "download_error",
                {
                    "user_id": user_id,
                    "platform": platform,
                    "error": error_message,
                    "processing_time": processing_time,
                },
            )

            logger.info(
                f"Tracked failed download: {user_id} from {platform}, error: {error_message}"
            )

        except Exception as e:
            logger.error(f"Failed to track download failure: {e}")

    def track_provider_attempt(self, platform: str):
        if not self._should_track_platform(platform):
            return
        try:
            self.rabbitmq.send_provider_stats(
                platform=platform, action="download_attempt", success=True
            )
            logger.debug(f"Tracked provider attempt: {platform}")
        except Exception as e:
            logger.error(f"Failed to track provider attempt: {e}")

    def track_bot_start(self):
        try:
            self.rabbitmq.send_bot_event("bot_started", {"timestamp": time.time()})
            logger.info("Tracked bot start")
        except Exception as e:
            logger.error(f"Failed to track bot start: {e}")

    def track_bot_stop(self):
        try:
            self.rabbitmq.send_bot_event("bot_stopped", {"timestamp": time.time()})
            logger.info("Tracked bot stop")
        except Exception as e:
            logger.error(f"Failed to track bot stop: {e}")

    def track_group_added(self, chat_id: int, title: str, chat_type: str):
        try:
            self.rabbitmq.send_bot_event(
                "group_added",
                {
                    "chat_id": chat_id,
                    "title": title,
                    "chat_type": chat_type,
                },
            )
            logger.info(f"Tracked group added: {chat_id} ({title})")
        except Exception as e:
            logger.error(f"Failed to track group added: {e}")

    def track_group_message(self, chat_id: int, title: str, chat_type: str):
        try:
            self.rabbitmq.send_bot_event(
                "group_message",
                {
                    "chat_id": chat_id,
                    "title": title,
                    "chat_type": chat_type,
                },
            )
            logger.debug(f"Tracked group message: {chat_id} ({title})")
        except Exception as e:
            logger.error(f"Failed to track group message: {e}")


stats_collector = StatsCollector()
