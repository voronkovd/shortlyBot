import glob
import logging
import os
import re
import subprocess  # nosec B404 - вызываем gallery-dl
import tempfile
from typing import List, Optional, Tuple, Union
from urllib.parse import urlparse

from providers.base import BaseProvider, KindId, MediaItem

logger = logging.getLogger(__name__)


class InstagramProvider(BaseProvider):
    platform = "instagram"
    PATTERNS = [
        ("post", r"instagram\.com/p/([^/]+)"),
        ("reels", r"instagram\.com/reels/([^/]+)"),
        ("reel", r"instagram\.com/reel/([^/]+)"),
        ("tv", r"instagram\.com/tv/([^/]+)"),
        ("story", r"instagram\.com/stories/[^/]+/([^/]+)"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if not host.endswith("instagram.com"):
                return False
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            return any(
                re.search(pat, clean, flags=re.IGNORECASE) for _, pat in self.PATTERNS
            )
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        if kind == "post":
            return f"https://www.instagram.com/p/{ident}/"
        if kind == "reel" or kind == "reels":
            return f"https://www.instagram.com/reels/{ident}/"
        if kind == "tv":
            return f"https://www.instagram.com/tv/{ident}/"
        if kind == "story":
            # для многих кейсов сториз потребуется cookie
            return f"https://www.instagram.com/stories/highlights/{ident}/"
        return f"https://www.instagram.com/p/{ident}/"

    def download_media(
        self, ref: Union[str, KindId]
    ) -> Tuple[List[MediaItem], Optional[str]]:
        """
        Для обычных постов (kind == "post") используем gallery-dl, чтобы забирать фото/карусели.
        Для остальных типов (reels/tv/story) падаем обратно на стандартный видео-процессинг.
        """
        if isinstance(ref, tuple):
            kind, ident = ref
        else:
            kind, ident = "post", ref

        if kind != "post":
            return super().download_media(ref)

        url = self._build_url(kind, ident)
        logger.info(f"Downloading Instagram post via gallery-dl: {url}")

        with tempfile.TemporaryDirectory() as temp_dir:
            cookies_path = (
                os.getenv("INSTAGRAM_COOKIES_FILE")
                or os.getenv("YTDLP_COOKIES_FILE_RUNTIME")
                or os.getenv("YTDLP_COOKIES_FILE")
            )
            cmd = [
                "gallery-dl",
            ]
            if cookies_path and os.path.exists(cookies_path):
                cmd += ["--cookies", cookies_path]
            cmd += [
                "-D",
                temp_dir,
                "--write-metadata",
                url,
            ]
            try:
                subprocess.run(cmd, check=True)  # nosec B603
            except Exception as e:
                logger.error(f"gallery-dl error for {url}: {e}")
                raise

            image_exts = ("jpg", "jpeg", "png", "webp")
            files: List[str] = []
            for ext in image_exts:
                files.extend(glob.glob(os.path.join(temp_dir, f"*.{ext}")))

            if not files:
                raise RuntimeError("Instagram photos not found after gallery-dl")

            media_items: List[MediaItem] = []
            for path in sorted(files):
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read downloaded image {path}: {e}")
                    continue

                media_items.append(
                    {
                        "kind": "photo",
                        "filename": os.path.basename(path),
                        "data": data,
                    }
                )

            if not media_items:
                raise RuntimeError("No readable Instagram photos after gallery-dl")

            caption: Optional[str] = None
            meta_files = glob.glob(os.path.join(temp_dir, "*.json"))
            if meta_files:
                try:
                    import json

                    with open(meta_files[0], "r", encoding="utf-8") as mf:
                        meta = json.load(mf)
                    caption = (
                        meta.get("description")
                        or meta.get("title")
                        or meta.get("content")
                    )
                    if caption:
                        caption = str(caption)[:1024]
                except Exception as e:
                    logger.debug(f"Failed to read Instagram metadata: {e}")

            return media_items, caption
