import re
from urllib.parse import urlparse

from providers.base import BaseProvider


class LikeeProvider(BaseProvider):
    platform = "likee"
    PATTERNS = [
        ("video", r"(?:likee\.video|likee\.com)/video/(\d+)"),
        ("video", r"(?:likee\.video|likee\.com)/@[^/]+/video/(\d+)"),
        ("video", r"(?:likee\.video|likee\.com)/v/(\d+)"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if not (host.endswith("likee.video") or host.endswith("likee.com")):
                return False
            clean = url.split("?", 1)[0].split("#", 1)[0]
            return any(
                re.search(p, clean, flags=re.IGNORECASE) for _, p in self.PATTERNS
            )
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        return f"https://likee.video/video/{ident}"
