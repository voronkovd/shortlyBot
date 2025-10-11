import pytest
import tempfile
from unittest.mock import Mock, patch
from providers.base import BaseProvider


class ConcreteProvider(BaseProvider):
    """Конкретная реализация BaseProvider для тестирования"""

    def __init__(self):
        self.platform = "test"
        self.PATTERNS = [
            ("video", r"test\.com/video/(\d+)"),
            ("clip", r"test\.com/clip/(\d+)"),
        ]

    def is_valid_url(self, url: str) -> bool:
        return "test.com" in url

    def _build_url(self, kind: str, ident: str) -> str:
        return f"https://test.com/{kind}/{ident}"


class TestBaseProvider:

    @pytest.fixture
    def provider(self):
        return ConcreteProvider()

    def test_extract_id_success(self, provider):
        """Тест успешного извлечения ID"""
        url = "https://test.com/video/123"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_extract_id_with_query_params(self, provider):
        """Тест извлечения ID с параметрами запроса"""
        url = "https://test.com/video/123?param=value"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_extract_id_with_fragment(self, provider):
        """Тест извлечения ID с фрагментом"""
        url = "https://test.com/video/123#fragment"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_extract_id_no_match(self, provider):
        """Тест извлечения ID без совпадения"""
        url = "https://other.com/video/123"
        result = provider.extract_id(url)

        assert result is None

    def test_extract_id_case_insensitive(self, provider):
        """Тест извлечения ID без учета регистра"""
        url = "https://TEST.COM/VIDEO/123"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_yt_opts(self, provider):
        """Тест настроек yt-dlp"""
        with tempfile.TemporaryDirectory() as temp_dir:
            opts = provider._yt_opts(temp_dir)

            # Проверяем основные настройки
            assert "outtmpl" in opts
            assert "format" in opts
            assert "quiet" in opts
            assert "no_warnings" in opts
            assert "extract_flat" in opts
            assert "writethumbnail" in opts
            assert "writeinfojson" in opts
            assert "noplaylist" in opts
            assert "retries" in opts
            assert "fragment_retries" in opts
            assert "skip_unavailable_fragments" in opts
            assert "concurrent_fragment_downloads" in opts
            assert "http_headers" in opts
            assert "socket_timeout" in opts

            # Проверяем значения
            assert opts["format"] == "best[height<=1080]/best"
            assert opts["quiet"] is True
            assert opts["no_warnings"] is True
            assert opts["extract_flat"] is False
            assert opts["writethumbnail"] is False
            assert opts["writeinfojson"] is False
            assert opts["noplaylist"] is True
            assert opts["retries"] == 5
            assert opts["fragment_retries"] == 5
            assert opts["skip_unavailable_fragments"] is True
            assert opts["concurrent_fragment_downloads"] == 1
            assert opts["socket_timeout"] == 60

            # Проверяем User-Agent
            assert "User-Agent" in opts["http_headers"]
            assert "Mozilla" in opts["http_headers"]["User-Agent"]

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_success(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        """Тест успешного скачивания видео"""
        # Настройка моков
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "description": "Test Description",
            "duration": 30,
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        # Мокаем открытие файла
        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        assert caption == "Test Video"

        # Проверяем, что методы были вызваны
        mock_ydl.extract_info.assert_called_once()
        mock_ydl.download.assert_called_once()

    @patch("providers.base.yt_dlp.YoutubeDL")
    def test_download_video_no_info(self, mock_ydl_class, provider):
        """Тест скачивания без информации о видео"""
        # Настройка моков
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = None

        with pytest.raises(RuntimeError, match="Failed to get video information"):
            provider.download_video(("video", "123"))

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    def test_download_video_no_files(self, mock_glob, mock_ydl_class, provider):
        """Тест скачивания без файлов"""
        # Настройка моков
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info
        mock_glob.return_value = []  # Нет файлов

        with pytest.raises(RuntimeError, match="Video file not found after download"):
            provider.download_video(("video", "123"))

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_with_string_ref(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        """Тест скачивания с строковым ref"""
        # Настройка моков
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        # Мокаем открытие файла
        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video("123")

        assert video_data == b"video_data"
        assert caption == "Test Video"

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_format_error_fallback(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        """Тест fallback при ошибке формата"""
        # Настройка моков
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info

        # Первый вызов download выбрасывает исключение
        mock_ydl.download.side_effect = [Exception("Format error"), None]

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        # Мокаем открытие файла
        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        assert caption == "Test Video"

        # Проверяем, что download был вызван дважды
        assert mock_ydl.download.call_count == 2


def mock_open_with_content(content):
    """Хелпер для мока открытия файла с содержимым"""
    mock_file = Mock()
    mock_file.read.return_value = content
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=None)
    return Mock(return_value=mock_file)
