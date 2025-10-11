import pytest
from unittest.mock import Mock, patch, MagicMock
from handlers.downloader import Downloader
from providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Мок провайдер для тестирования"""
    
    def __init__(self, platform_name, valid_urls=None, extract_result=None, download_result=None):
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
        """Создает мок провайдеры для тестирования"""
        providers = [
            MockProvider("instagram", ["https://instagram.com/p/123/"], ("post", "123"), (b"video_data", "caption")),
            MockProvider("tiktok", ["https://tiktok.com/video/456"], ("video", "456"), (b"video_data", "caption")),
            MockProvider("youtube", ["https://youtube.com/shorts/789"], ("shorts", "789"), (b"video_data", "caption"))
        ]
        return providers
    
    @pytest.fixture
    def downloader(self, mock_providers):
        """Создает Downloader с мок провайдерами"""
        with patch('handlers.downloader.Downloader.__init__', return_value=None):
            downloader = Downloader()
            downloader.downloaders = mock_providers
            return downloader
    
    def test_get_downloader_found(self, downloader):
        """Тест поиска подходящего провайдера"""
        url = "https://instagram.com/p/123/"
        provider = downloader.get_downloader(url)
        
        assert provider is not None
        assert provider.platform == "instagram"
    
    def test_get_downloader_not_found(self, downloader):
        """Тест случая, когда провайдер не найден"""
        url = "https://unknown-platform.com/video/123"
        provider = downloader.get_downloader(url)
        
        assert provider is None
    
    def test_download_video_success(self, downloader):
        """Тест успешного скачивания видео"""
        url = "https://instagram.com/p/123/"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data == b"video_data"
        assert caption == "caption"
        assert platform == "mockprovider"
    
    def test_download_video_no_provider(self, downloader):
        """Тест скачивания без подходящего провайдера"""
        url = "https://unknown-platform.com/video/123"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data is None
        assert caption is None
        assert platform is None
    
    def test_download_video_no_extract_id(self, downloader):
        """Тест скачивания без возможности извлечь ID"""
        # Создаем провайдер, который не может извлечь ID
        mock_provider = MockProvider("test", ["https://test.com/video/123"], None, None)
        downloader.downloaders = [mock_provider]
        
        url = "https://test.com/video/123"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data is None
        assert caption is None
        assert platform is None
    
    def test_download_video_provider_exception(self, downloader):
        """Тест обработки исключения от провайдера"""
        # Создаем провайдер, который выбрасывает исключение
        mock_provider = MockProvider("test", ["https://test.com/video/123"], ("video", "123"), None)
        mock_provider.download_video = Mock(side_effect=Exception("Download failed"))
        downloader.downloaders = [mock_provider]
        
        url = "https://test.com/video/123"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data is None
        assert caption is None
        assert platform is None
    
    def test_download_video_with_tuple_ref(self, downloader):
        """Тест скачивания с передачей tuple в качестве ref"""
        # Создаем провайдер, который принимает tuple
        mock_provider = MockProvider("test", ["https://test.com/video/123"], ("video", "123"), (b"video_data", "caption"))
        downloader.downloaders = [mock_provider]
        
        url = "https://test.com/video/123"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data == b"video_data"
        assert caption == "caption"
        assert platform == "mockprovider"
    
    def test_download_video_empty_result(self, downloader):
        """Тест скачивания с пустым результатом"""
        # Создаем провайдер, который возвращает пустой результат
        mock_provider = MockProvider("test", ["https://test.com/video/123"], ("video", "123"), (None, "caption"))
        downloader.downloaders = [mock_provider]
        
        url = "https://test.com/video/123"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data is None
        assert caption is None
        assert platform is None
    
    def test_download_video_string_ref(self, downloader):
        """Тест скачивания с передачей строки в качестве ref"""
        # Создаем провайдер, который принимает строку
        mock_provider = MockProvider("test", ["https://test.com/video/123"], ("video", "123"), (b"video_data", "caption"))
        downloader.downloaders = [mock_provider]
        
        url = "https://test.com/video/123"
        
        video_data, caption, platform = downloader.download_video(url)
        
        assert video_data == b"video_data"
        assert caption == "caption"
        assert platform == "mockprovider"
