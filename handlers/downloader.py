import logging
from typing import List, Optional, Tuple

from providers.base import BaseProvider
from providers.facebook import FacebookProvider
from providers.instagram import InstagramProvider
from providers.likee import LikeeProvider
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

            if video_data:
                logger.info(f"Video successfully downloaded from {platform}")
                return video_data, caption, platform
            else:
                logger.error(f"Failed to download video from {platform}")
                return None, None, None

        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, None, None
