import pytest

from providers.facebook import FacebookProvider
from providers.instagram import InstagramProvider
from providers.likee import LikeeProvider
from providers.rutube import RuTubeProvider
from providers.tiktok import TikTokProvider
from providers.youtube import YouTubeProvider


class TestInstagramProvider:

    @pytest.fixture
    def provider(self):
        return InstagramProvider()

    def test_platform_name(self, provider):
        assert provider.platform == "instagram"

    def test_valid_urls(self, provider):
        """Тест валидных URL Instagram"""
        valid_urls = [
            "https://www.instagram.com/p/ABC123/",
            "https://instagram.com/reel/XYZ789/",
            "https://www.instagram.com/tv/DEF456/",
            "https://instagram.com/p/ABC123/?utm_source=ig_web_copy_link",
        ]

        for url in valid_urls:
            assert provider.is_valid_url(url), f"URL should be valid: {url}"

    def test_invalid_urls(self, provider):
        """Тест невалидных URL"""
        invalid_urls = [
            "https://www.youtube.com/watch?v=123",
            "https://tiktok.com/@user/video/123",
            "https://instagram.com/user/",
            "not_a_url",
            "",
        ]

        for url in invalid_urls:
            assert not provider.is_valid_url(url), f"URL should be invalid: {url}"

    def test_extract_id(self, provider):
        """Тест извлечения ID из URL"""
        test_cases = [
            ("https://www.instagram.com/p/ABC123/", ("post", "ABC123")),
            ("https://instagram.com/reel/XYZ789/", ("reel", "XYZ789")),
            ("https://www.instagram.com/tv/DEF456/", ("tv", "DEF456")),
        ]

        for url, expected in test_cases:
            result = provider.extract_id(url)
            assert result == expected, f"Expected {expected}, got {result} for {url}"

    def test_build_url(self, provider):
        """Тест построения URL"""
        test_cases = [
            (("post", "ABC123"), "https://www.instagram.com/p/ABC123/"),
            (("reel", "XYZ789"), "https://www.instagram.com/reel/XYZ789/"),
            (("tv", "DEF456"), "https://www.instagram.com/tv/DEF456/"),
        ]

        for (kind, ident), expected in test_cases:
            result = provider._build_url(kind, ident)
            assert result == expected


class TestTikTokProvider:

    @pytest.fixture
    def provider(self):
        return TikTokProvider()

    def test_platform_name(self, provider):
        assert provider.platform == "tiktok"

    def test_valid_urls(self, provider):
        """Тест валидных URL TikTok"""
        valid_urls = [
            "https://www.tiktok.com/@user/video/1234567890",
            "https://tiktok.com/@user/video/1234567890",
            "https://vm.tiktok.com/ABC123",
            "https://vt.tiktok.com/XYZ789",
        ]

        for url in valid_urls:
            assert provider.is_valid_url(url), f"URL should be valid: {url}"

    def test_extract_id(self, provider):
        """Тест извлечения ID из URL"""
        test_cases = [
            ("https://www.tiktok.com/@user/video/1234567890", ("video", "1234567890")),
            ("https://vm.tiktok.com/ABC123", ("short", "ABC123")),
        ]

        for url, expected in test_cases:
            result = provider.extract_id(url)
            assert result == expected, f"Expected {expected}, got {result} for {url}"


class TestYouTubeProvider:

    @pytest.fixture
    def provider(self):
        return YouTubeProvider()

    def test_platform_name(self, provider):
        assert provider.platform == "youtube"

    def test_valid_urls(self, provider):
        """Тест валидных URL YouTube"""
        valid_urls = [
            "https://www.youtube.com/shorts/ABC123",
            "https://youtu.be/ABC123",
        ]

        for url in valid_urls:
            assert provider.is_valid_url(url), f"URL should be valid: {url}"

    def test_extract_id(self, provider):
        """Тест извлечения ID из URL"""
        test_cases = [
            ("https://www.youtube.com/shorts/ABC123", ("watch", "ABC123")),
            ("https://youtu.be/ABC123", ("watch", "ABC123")),
        ]

        for url, expected in test_cases:
            result = provider.extract_id(url)
            assert result == expected, f"Expected {expected}, got {result} for {url}"


class TestLikeeProvider:

    @pytest.fixture
    def provider(self):
        return LikeeProvider()

    def test_platform_name(self, provider):
        assert provider.platform == "likee"

    def test_valid_urls(self, provider):
        """Тест валидных URL Likee"""
        valid_urls = [
            "https://likee.video/video/123456789",
            "https://likee.com/video/123456789",
            "https://likee.video/@user/video/123456789",
        ]

        for url in valid_urls:
            assert provider.is_valid_url(url), f"URL should be valid: {url}"

    def test_extract_id(self, provider):
        """Тест извлечения ID из URL"""
        test_cases = [
            ("https://likee.video/video/123456789", ("video", "123456789")),
            ("https://likee.video/@user/video/123456789", ("video", "123456789")),
        ]

        for url, expected in test_cases:
            result = provider.extract_id(url)
            assert result == expected, f"Expected {expected}, got {result} for {url}"


class TestFacebookProvider:

    @pytest.fixture
    def provider(self):
        return FacebookProvider()

    def test_platform_name(self, provider):
        assert provider.platform == "facebook"

    def test_valid_urls(self, provider):
        """Тест валидных URL Facebook"""
        valid_urls = [
            "https://www.facebook.com/reel/123456789",
            "https://fb.watch/ABC123",
        ]

        for url in valid_urls:
            assert provider.is_valid_url(url), f"URL should be valid: {url}"


class TestRuTubeProvider:

    @pytest.fixture
    def provider(self):
        return RuTubeProvider()

    def test_platform_name(self, provider):
        assert provider.platform == "rutube"

    def test_valid_urls(self, provider):
        """Тест валидных URL RuTube"""
        valid_urls = [
            "https://rutube.ru/video/abc123def456",
            "https://rutube.ru/shorts/cea63c15281278af170cdaec2115cf87",
            "https://rutube.ru/play/embed/123456",
        ]

        for url in valid_urls:
            assert provider.is_valid_url(url), f"URL should be valid: {url}"

    def test_extract_id(self, provider):
        """Тест извлечения ID из URL"""
        test_cases = [
            ("https://rutube.ru/video/abc123def456", ("video", "abc123def456")),
            (
                "https://rutube.ru/shorts/cea63c15281278af170cdaec2115cf87",
                ("shorts", "cea63c15281278af170cdaec2115cf87"),
            ),
            ("https://rutube.ru/play/embed/123456", ("embed", "123456")),
        ]

        for url, expected in test_cases:
            result = provider.extract_id(url)
            assert result == expected, f"Expected {expected}, got {result} for {url}"

    def test_build_url(self, provider):
        """Тест построения URL"""
        test_cases = [
            (("video", "abc123def456"), "https://rutube.ru/video/abc123def456/"),
            (
                ("shorts", "cea63c15281278af170cdaec2115cf87"),
                "https://rutube.ru/shorts/cea63c15281278af170cdaec2115cf87/",
            ),
            (("embed", "123456"), "https://rutube.ru/video/123456/"),
        ]

        for (kind, ident), expected in test_cases:
            result = provider._build_url(kind, ident)
            assert result == expected
