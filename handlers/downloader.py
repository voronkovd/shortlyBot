import logging
from typing import List, Optional, Tuple

from providers.base import BaseProvider, MediaItem
from providers.facebook import FacebookProvider
from providers.instagram import InstagramProvider
from providers.likee import LikeeProvider
from providers.reddit import RedditProvider
from providers.rutube import RuTubeProvider
from providers.tiktok import TikTokProvider
from providers.youtube import YouTubeProvider

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self):
        self.downloaders: List[BaseProvider] = [
            InstagramProvider(),
            TikTokProvider(),
            YouTubeProvider(),
            LikeeProvider(),
            FacebookProvider(),
            RuTubeProvider(),
            RedditProvider(),
        ]
        logger.info(f"Initialized manager with {len(self.downloaders)} downloaders")

    def get_downloader(self, url: str) -> Optional[BaseProvider]:
        for downloader in self.downloaders:
            if downloader.is_valid_url(url):
                logger.info(
                    f"Found suitable downloader: {downloader.__class__.__name__}"
                )
                return downloader

        logger.warning("No suitable downloader found")
        return None

    def download_video(
        self, url: str
    ) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        logger.info(f"Starting video download for URL: {url}")

        downloader = self.get_downloader(url)
        if not downloader:
            return None, None, None

        video_id = downloader.extract_id(url)
        if not video_id:
            logger.error("Failed to extract video ID")
            return None, None, None

        logger.info(f"Extracted ID: {video_id}")

        try:
            video_data, caption = downloader.download_video(video_id)
            platform = getattr(
                downloader,
                "platform",
                downloader.__class__.__name__.replace("Provider", "").lower(),
            )
            # Если platform пустая строка, используем fallback
            if not platform:
                platform = downloader.__class__.__name__.replace("Provider", "").lower()

            if video_data:
                logger.info(f"Video successfully downloaded from {platform}")
                return video_data, caption, platform
            else:
                logger.error(f"Failed to download video from {platform}")
                return None, None, platform

        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, None, None

    def download_media(
        self, url: str
    ) -> Tuple[Optional[List[MediaItem]], Optional[str], Optional[str]]:
        """
        Новый метод: возвращает список медиа (фото/видео) и подпись.
        Для всех провайдеров, кроме Instagram, базовая реализация даёт один элемент-видео.
        """
        logger.info(f"Starting media download for URL: {url}")

        downloader = self.get_downloader(url)
        if not downloader:
            return None, None, None

        media_id = downloader.extract_id(url)
        if not media_id:
            logger.error("Failed to extract media ID")
            return None, None, None

        logger.info(f"Extracted ID: {media_id}")

        try:
            media_items, caption = downloader.download_media(media_id)
            platform = getattr(
                downloader,
                "platform",
                downloader.__class__.__name__.replace("Provider", "").lower(),
            )
            if not platform:
                platform = downloader.__class__.__name__.replace("Provider", "").lower()

            if media_items:
                logger.info(f"Media successfully downloaded from {platform}")
                return media_items, caption, platform
            else:
                logger.error(f"Failed to download media from {platform}")
                return None, None, platform

        except Exception as e:
            logger.error(f"Media download error: {e}")
            return None, None, None
