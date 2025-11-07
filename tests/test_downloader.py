from unittest.mock import Mock, patch

import pytest

from handlers.downloader import Downloader
from providers.base import BaseProvider


class MockProvider(BaseProvider):
    def __init__(
        self, platform_name, valid_urls=None, extract_result=None, download_result=None
    ):
        self.platform = platform_name
        self.valid_urls = valid_urls or []
        self.extract_result = extract_result
        self.download_result = download_result

    def is_valid_url(self, url: str) -> bool:
        return url in self.valid_urls

    def _build_url(self, kind: str, ident: str) -> str:
        return f"https://{self.platform}.com/{kind}/{ident}"

    def extract_id(self, url: str):
        return self.extract_result

    def download_video(self, ref):
        return self.download_result


class TestDownloader:

    @pytest.fixture
    def mock_providers(self):
        providers = [
            MockProvider(
                "instagram",
                ["https://instagram.com/p/123/"],
                ("post", "123"),
                (b"video_data", "caption"),
            ),
            MockProvider(
                "tiktok",
                ["https://tiktok.com/video/456"],
                ("video", "456"),
                (b"video_data", "caption"),
            ),
            MockProvider(
                "youtube",
                ["https://youtube.com/shorts/789"],
                ("shorts", "789"),
                (b"video_data", "caption"),
            ),
        ]
        return providers

    @pytest.fixture
    def downloader(self, mock_providers):
        with patch("handlers.downloader.Downloader.__init__", return_value=None):
            downloader = Downloader()
            downloader.downloaders = mock_providers
            return downloader

    def test_get_downloader_found(self, downloader):
        url = "https://instagram.com/p/123/"
        provider = downloader.get_downloader(url)

        assert provider is not None
        assert provider.platform == "instagram"

    def test_get_downloader_not_found(self, downloader):
        url = "https://unknown-platform.com/video/123"
        provider = downloader.get_downloader(url)

        assert provider is None

    def test_download_video_success(self, downloader):
        url = "https://instagram.com/p/123/"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data == b"video_data"
        assert caption == "caption"
        assert platform == "instagram"

    def test_download_video_no_provider(self, downloader):
        url = "https://unknown-platform.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data is None
        assert caption is None
        assert platform is None

    def test_download_video_no_extract_id(self, downloader):
        mock_provider = MockProvider("test", ["https://test.com/video/123"], None, None)
        downloader.downloaders = [mock_provider]

        url = "https://test.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data is None
        assert caption is None
        assert platform is None

    def test_download_video_provider_exception(self, downloader):
        mock_provider = MockProvider(
            "test", ["https://test.com/video/123"], ("video", "123"), None
        )
        mock_provider.download_video = Mock(side_effect=Exception("Download failed"))
        downloader.downloaders = [mock_provider]

        url = "https://test.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data is None
        assert caption is None
        assert platform is None

    def test_download_video_with_tuple_ref(self, downloader):
        mock_provider = MockProvider(
            "test",
            ["https://test.com/video/123"],
            ("video", "123"),
            (b"video_data", "caption"),
        )
        downloader.downloaders = [mock_provider]

        url = "https://test.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data == b"video_data"
        assert caption == "caption"
        assert platform == "test"

    def test_download_video_empty_result(self, downloader):
        mock_provider = MockProvider(
            "test", ["https://test.com/video/123"], ("video", "123"), (None, "caption")
        )
        downloader.downloaders = [mock_provider]

        url = "https://test.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data is None
        assert caption is None
        assert platform == "test"  # Платформа возвращается даже если видео не скачалось

    def test_download_video_string_ref(self, downloader):
        mock_provider = MockProvider(
            "test",
            ["https://test.com/video/123"],
            ("video", "123"),
            (b"video_data", "caption"),
        )
        downloader.downloaders = [mock_provider]

        url = "https://test.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data == b"video_data"
        assert caption == "caption"
        assert platform == "test"

    def test_download_video_empty_platform_fallback(self, downloader):
        """Тест проверяет, что при пустой платформе используется fallback из имени класса"""
        mock_provider = MockProvider(
            "",  # Пустая платформа
            ["https://test.com/video/123"],
            ("video", "123"),
            (b"video_data", "caption"),
        )
        downloader.downloaders = [mock_provider]

        url = "https://test.com/video/123"

        video_data, caption, platform = downloader.download_video(url)

        assert video_data == b"video_data"
        assert caption == "caption"
        # Должен использоваться fallback из имени класса (MockProvider -> mock)
        assert platform == "mock"
