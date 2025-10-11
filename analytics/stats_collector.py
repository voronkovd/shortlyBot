import time
import logging
from typing import Optional
from .rabbitmq_client import rabbitmq_client

logger = logging.getLogger(__name__)


class StatsCollector:
    """Коллектор статистики для бота"""
    
    def __init__(self):
        self.rabbitmq = rabbitmq_client
    
    def track_user_request(self, user_id: int, username: str, platform: str):
        """Отслеживает запрос пользователя на скачивание"""
        try:
            self.rabbitmq.send_user_stats(
                user_id=user_id,
                username=username or "unknown",
                action="download_request",
                platform=platform,
                success=True
            )
            logger.info(f"Tracked user request: {user_id} for {platform}")
        except Exception as e:
            logger.error(f"Failed to track user request: {e}")
    
    def track_download_success(self, user_id: int, username: str, platform: str, 
                              video_size: int, processing_time: float):
        """Отслеживает успешное скачивание"""
        try:
            # Статистика пользователя
            self.rabbitmq.send_user_stats(
                user_id=user_id,
                username=username or "unknown",
                action="download_success",
                platform=platform,
                success=True
            )
            
            # Статистика провайдера
            self.rabbitmq.send_provider_stats(
                platform=platform,
                action="download_success",
                success=True,
                video_size=video_size,
                processing_time=processing_time
            )
            
            logger.info(f"Tracked successful download: {user_id} from {platform}, size: {video_size} bytes, time: {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to track download success: {e}")
    
    def track_download_failure(self, user_id: int, username: str, platform: str, 
                              error_message: str, processing_time: Optional[float] = None):
        """Отслеживает неудачное скачивание"""
        try:
            # Статистика пользователя
            self.rabbitmq.send_user_stats(
                user_id=user_id,
                username=username or "unknown",
                action="download_failed",
                platform=platform,
                success=False
            )
            
            # Статистика провайдера
            self.rabbitmq.send_provider_stats(
                platform=platform,
                action="download_failed",
                success=False,
                processing_time=processing_time
            )
            
            # Общее событие с ошибкой
            self.rabbitmq.send_bot_event("download_error", {
                "user_id": user_id,
                "platform": platform,
                "error": error_message,
                "processing_time": processing_time
            })
            
            logger.info(f"Tracked failed download: {user_id} from {platform}, error: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to track download failure: {e}")
    
    def track_provider_attempt(self, platform: str):
        """Отслеживает попытку использования провайдера"""
        try:
            self.rabbitmq.send_provider_stats(
                platform=platform,
                action="download_attempt",
                success=True
            )
            logger.debug(f"Tracked provider attempt: {platform}")
        except Exception as e:
            logger.error(f"Failed to track provider attempt: {e}")
    
    def track_bot_start(self):
        """Отслеживает запуск бота"""
        try:
            self.rabbitmq.send_bot_event("bot_started", {
                "timestamp": time.time()
            })
            logger.info("Tracked bot start")
        except Exception as e:
            logger.error(f"Failed to track bot start: {e}")
    
    def track_bot_stop(self):
        """Отслеживает остановку бота"""
        try:
            self.rabbitmq.send_bot_event("bot_stopped", {
                "timestamp": time.time()
            })
            logger.info("Tracked bot stop")
        except Exception as e:
            logger.error(f"Failed to track bot stop: {e}")


# Глобальный экземпляр коллектора
stats_collector = StatsCollector()
