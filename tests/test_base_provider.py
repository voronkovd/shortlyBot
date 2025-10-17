import re
import tempfile
from unittest.mock import Mock, patch

import pytest

from providers.base import BaseProvider


class ConcreteProvider(BaseProvider):

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
        url = "https://test.com/video/123"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_extract_id_with_query_params(self, provider):
        url = "https://test.com/video/123?param=value"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_extract_id_with_fragment(self, provider):
        url = "https://test.com/video/123#fragment"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_extract_id_no_match(self, provider):
        url = "https://other.com/video/123"
        result = provider.extract_id(url)

        assert result is None

    def test_extract_id_case_insensitive(self, provider):
        url = "https://TEST.COM/VIDEO/123"
        result = provider.extract_id(url)

        assert result == ("video", "123")

    def test_yt_opts(self, provider):
        with tempfile.TemporaryDirectory() as temp_dir:
            opts = provider._yt_opts(temp_dir)

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

            fmt = opts.get("format", "")

            assert (
                fmt == "best[height<=1080]/best"
                or ("vcodec=h264" in fmt and "ext=mp4" in fmt)
                or (re.search(r"height<=\s*1080", fmt) is not None)
            ), f"Unexpected format value: {fmt}"

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

            assert "User-Agent" in opts["http_headers"]
            assert "Mozilla" in opts["http_headers"]["User-Agent"]

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_success(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "description": "Test Description",
            "duration": 30,
            "uploader": "test_user",
            "uploader_id": "testuser123",
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        expected_caption = "Test Video\n\nTest Description\n\nVideo by @testuser123"
        assert caption == expected_caption

        mock_ydl.extract_info.assert_called_once()
        mock_ydl.download.assert_called_once()

    @patch("providers.base.yt_dlp.YoutubeDL")
    def test_download_video_no_info(self, mock_ydl_class, provider):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = None

        with pytest.raises(RuntimeError, match="Failed to get video information"):
            provider.download_video(("video", "123"))

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    def test_download_video_no_files(self, mock_glob, mock_ydl_class, provider):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info
        mock_glob.return_value = []

        with pytest.raises(RuntimeError, match="Video file not found after download"):
            provider.download_video(("video", "123"))

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_with_string_ref(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

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
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {"title": "Test Video"}
        mock_ydl.extract_info.return_value = mock_info

        mock_ydl.download.side_effect = [Exception("Format error"), None]

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        assert caption == "Test Video"

        assert mock_ydl.download.call_count == 2

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_with_uploader_only(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "duration": 30,
            "uploader": "Test User",
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        expected_caption = "Test Video\n\nVideo by @testuser"
        assert caption == expected_caption

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_with_channel_info(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "duration": 30,
            "channel": "Test Channel",
            "channel_id": "testchannel456",
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        expected_caption = "Test Video\n\nVideo by @testchannel456"
        assert caption == expected_caption

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_no_attribution(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "duration": 30,
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        assert caption == "Test Video"

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_same_title_description(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Test Video",
            "description": "Test Video",  # То же самое что title
            "duration": 30,
            "uploader": "test_user",
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            video_data, caption = provider.download_video(("video", "123"))

        assert video_data == b"video_data"
        expected_caption = "Test Video\n\nVideo by @test_user"
        assert caption == expected_caption

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_description_only(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "description": "Only description available",
            "duration": 30,
            "uploader": None,
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            _, caption = provider.download_video(("video", "123"))

        assert caption == "Only description available"

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_channel_without_id(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        mock_info = {
            "title": "Channel Video",
            "duration": 30,
            "channel": "Test Channel Name",
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            _, caption = provider.download_video(("video", "123"))

        expected_caption = "Channel Video\n\nVideo by @testchannelname"
        assert caption == expected_caption

    @patch("providers.base.yt_dlp.YoutubeDL")
    @patch("providers.base.glob.glob")
    @patch("providers.base.os.path.getsize")
    def test_download_video_caption_truncates(
        self, mock_getsize, mock_glob, mock_ydl_class, provider
    ):
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        long_title = "T" * 512
        long_description = "D" * 800
        mock_info = {
            "title": long_title,
            "description": long_description,
            "duration": 30,
            "uploader": "Test User",
        }
        mock_ydl.extract_info.return_value = mock_info

        mock_glob.return_value = ["/tmp/test_video.mp4"]
        mock_getsize.return_value = 1024000

        with patch("builtins.open", mock_open_with_content(b"video_data")):
            _, caption = provider.download_video(("video", "123"))

        full_caption = f"{long_title}\n\n{long_description}\n\nVideo by @testuser"
        assert len(full_caption) > 1024
        expected_caption = full_caption[:1024]
        assert caption == expected_caption
        assert len(caption) == 1024


def mock_open_with_content(content):
    mock_file = Mock()
    mock_file.read.return_value = content
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=None)
    return Mock(return_value=mock_file)
