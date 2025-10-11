import re
from urllib.parse import urlparse
from providers.base import BaseProvider

class RuTubeProvider(BaseProvider):
    platform = "rutube"
    PATTERNS = [
        ("video",  r"rutube\.ru/video/([a-f0-9\-]{8,})"),
        ("embed",  r"rutube\.ru/(?:play|video)/embed/(\d+)"),
        ("video",  r"rutube\.ru/video/(\d+)"),
        ("shorts", r"rutube\.ru/shorts/([a-f0-9]{32})"),
    ]

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if not host.endswith("rutube.ru"):
                return False
            clean = url.split("?", 1)[0].split("#", 1)[0]
            return any(re.search(p, clean, flags=re.IGNORECASE) for _, p in self.PATTERNS)
        except Exception:
            return False

    def _build_url(self, kind: str, ident: str) -> str:
        if kind == "shorts":
            return f"https://rutube.ru/shorts/{ident}/"
        return f"https://rutube.ru/video/{ident}/"
