import glob
import logging
import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union

import yt_dlp

logger = logging.getLogger(__name__)

# (тип ресурса, id) — например: ("reel", "C9AbcDe"), ("watch", "1234567890")
KindId = Tuple[str, str]


class BaseProvider(ABC):
    PATTERNS: List[Tuple[str, str]] = []
    platform: str = ""  # например, "instagram", "tiktok"

    def extract_id(self, url: str) -> Optional[KindId]:
        clean = url.split("?", 1)[0].split("#", 1)[0]
        for kind, pattern in self.PATTERNS:
            m = re.search(pattern, clean, flags=re.IGNORECASE)
            if m:
                return kind, m.group(1)
        return None

    @abstractmethod
    def is_valid_url(self, url: str) -> bool: ...

    @abstractmethod
    def _build_url(self, kind: str, ident: str) -> str: ...

    def _yt_opts(self, temp_dir: str) -> Dict:
        opts = {
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
            "format": "best[height<=1080]/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writethumbnail": False,
            "writeinfojson": False,
            "noplaylist": True,
            "retries": 5,
            "fragment_retries": 5,
            "skip_unavailable_fragments": True,
            "concurrent_fragment_downloads": 1,
            "socket_timeout": 60,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            },
        }
        # cookiefile = os.getenv("YTDLP_COOKIES_FILE")
        # if cookiefile and os.path.exists(cookiefile):
        #     opts["cookiefile"] = cookiefile
        return opts

    def download_video(
        self, ref: Union[str, KindId]
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if isinstance(ref, tuple):
            kind, ident = ref
        else:
            kind, ident = "post", ref  # дефолт

        platform_name = (
            self.platform or self.__class__.__name__.replace("Downloader", "").lower()
        )
        logger.info(f"🔍 Starting {platform_name} {kind} download for ID: {ident}")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                ydl_opts = self._yt_opts(temp_dir)
                url = self._build_url(kind, ident)
                logger.info(f"Downloading via yt-dlp: {url}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        raise RuntimeError("Failed to get video information")
                    logger.info(
                        f"Title: {info.get('title')!r}, duration: {info.get('duration')}"
                    )

                    try:
                        ydl.download([url])
                    except Exception as format_error:
                        logger.warning(
                            f"Format error: {format_error} → fallback to 'best'"
                        )
                        ydl_opts["format"] = "best"
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            ydl2.download([url])

                files = []
                for ext in ("mp4", "webm", "mkv", "mov"):
                    files.extend(glob.glob(os.path.join(temp_dir, f"*.{ext}")))
                if not files:
                    raise RuntimeError("Video file not found after download")

                video_file = max(files, key=lambda p: os.path.getsize(p))
                logger.info(
                    f"📁 Selected file: {os.path.basename(video_file)} ({os.path.getsize(video_file)} bytes)"
                )

                with open(video_file, "rb") as f:
                    data = f.read()

                caption = info.get("title") or info.get("description") or ""
                if caption:
                    logger.info(f"Caption preview: {caption[:80]}...")

                return data, caption

            except Exception as e:
                logger.error(f"yt-dlp error: {e}")
                raise
