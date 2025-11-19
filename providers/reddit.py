import re
from urllib.parse import urlparse

from providers.base import BaseProvider


class RedditProvider(BaseProvider):
    platform = "reddit"
    PATTERNS = [
        ("post", r"reddit\.com/r/[^/]+/comments/([a-z0-9]+)"),
        ("post", r"reddit\.com/comments/([a-z0-9]+)"),
        ("post", r"redd\.it/([a-z0-9]+)"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if not (host.endswith("reddit.com") or host.endswith("redd.it")):
                return False
            clean = url.split("?", 1)[0].split("#", 1)[0]
            return any(
                re.search(p, clean, flags=re.IGNORECASE) for _, p in self.PATTERNS
            )
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        # yt-dlp поддерживает Reddit, можно передать полный URL
        # Используем формат с /comments/ для универсальности
        return f"https://www.reddit.com/comments/{ident}/"

