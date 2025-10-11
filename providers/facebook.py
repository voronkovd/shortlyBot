import re
from urllib.parse import urlparse

from providers.base import BaseProvider


class FacebookProvider(BaseProvider):
    platform = "facebook"
    PATTERNS = [
        ("reel", r"facebook\.com/reel/(\d+)"),
        ("watch", r"facebook\.com/.+?/videos/(\d+)"),
        ("short", r"fb\.watch/([^/?#]+)"),
        ("watch", r"facebook\.com/watch/\?v=(\d+)"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            valid = host.endswith("facebook.com") or host.startswith("fb.watch")
            if not valid:
                return False
            clean = url.split("?", 1)[0].split("#", 1)[0]
            return any(
                re.search(p, clean, flags=re.IGNORECASE) for _, p in self.PATTERNS
            )
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        if kind == "reel" and ident.isdigit():
            return f"https://www.facebook.com/reel/{ident}/"
        if kind == "watch" and ident.isdigit():
            return f"https://www.facebook.com/watch/?v={ident}"
        return f"https://fb.watch/{ident}/"
