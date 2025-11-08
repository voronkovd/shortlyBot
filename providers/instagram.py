import re
from urllib.parse import urlparse

from providers.base import BaseProvider


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
