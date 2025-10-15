import glob
import logging
import os
import re
import shutil
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
            # Приоритет: H.264 MP4 → готовый MP4 → любой best
            "format": "bv*[ext=mp4][vcodec=h264]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
            # Объединяем дорожки и оставляем mp4-контейнер
            "merge_output_format": "mp4",
            # Достаточно ремакса в MP4; конвертер обычно не нужен
            "postprocessors": [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
            ],
            # Аргументы для финального вызова ffmpeg (на выход)
            "postprocessor_args": {
                "ffmpeg_o": ["-movflags", "+faststart"],
            },
            # Тихий режим + ожидаемые тестом ключи
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
            "windowsfilenames": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
            },
            "compat_opts": ["no-keep-subs", "no-attach-info-json"],
            "prefer_free_formats": False,
        }

        # Куки: копируем в temp, чтобы не трогать ro-монты
        cookie_src = os.getenv("YTDLP_COOKIES_FILE_RUNTIME") or os.getenv(
            "YTDLP_COOKIES_FILE"
        )
        if cookie_src and os.path.exists(cookie_src):
            try:
                cookie_dst = os.path.join(temp_dir, "yt_cookies.txt")
                shutil.copyfile(cookie_src, cookie_dst)
                os.chmod(cookie_dst, 0o600)
                opts["cookiefile"] = cookie_dst
            except Exception as e:
                logger.warning(f"Cannot prepare cookiefile: {e}")

        # Сортировка форматов: сначала по высоте, потом кодек/контейнер/качество
        max_h = int(os.getenv("MAX_HEIGHT", "1080"))
        opts["format_sort"] = [
            f"res:{max_h}",
            "codec:h264",
            "ext:mp4",
            "fps",
            "vbr",
            "abr",
        ]

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
