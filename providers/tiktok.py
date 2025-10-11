import re
from urllib.parse import urlparse

from providers.base import BaseProvider


class TikTokProvider(BaseProvider):
    platform = "tiktok"
    PATTERNS = [
        ("video", r"tiktok\.com/@[^/]+/video/(\d+)"),
        ("short", r"tiktok\.com/t/([^/?#]+)"),
        ("short", r"vm\.tiktok\.com/([^/?#]+)"),
        ("short", r"vt\.tiktok\.com/([^/?#]+)"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if "tiktok.com" not in host:
                return False
            clean = url.split("?", 1)[0].split("#", 1)[0]
            return any(
                re.search(p, clean, flags=re.IGNORECASE) for _, p in self.PATTERNS
            )
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        if kind == "video" and ident.isdigit():
            # username неизвестен — yt-dlp понимает такой формат
            return f"https://www.tiktok.com/@_/video/{ident}"
        # короткие редиректы
        return f"https://www.tiktok.com/t/{ident}"
