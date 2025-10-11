import re
from urllib.parse import urlparse
from providers.base import BaseProvider

class YouTubeProvider(BaseProvider):
    platform = "youtube"
    PATTERNS = [
        ("watch",  r"youtube\.com/shorts/([^/?#]+)"),
        ("watch",  r"youtu\.be/([^/?#]+)"),
        ("watch",  r"youtube\.com/watch\?v=([^&#]+)"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if not (host.endswith("youtube.com") or host.endswith("youtu.be")):
                return False
            clean = url.split("?", 1)[0].split("#", 1)[0]
            return any(re.search(p, clean, flags=re.IGNORECASE) for _, p in self.PATTERNS)
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        return f"https://www.youtube.com/watch?v={ident}"
