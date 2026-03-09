"""Tests for YouTube API base datafeeds."""

from unittest import mock

import pytest

from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.tasks_io.datafeeds.datafeed_youtube import YoutubeApiBase
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class _MockYoutubeDatafeed(YoutubeApiBase):
    """Mock YouTube datafeed for testing base class."""

    def __init__(self) -> None:
        super().__init__()

    def endpoint(self) -> str:
        return "videos"

    def url_params(self) -> dict:
        return {
            "part": "snippet",
            "id": "test_video_id",
        }

    def parser(self) -> ParserBase:
        raise NotImplementedError("Mock parser not needed for these tests")


class TestYoutubeApiBase:
    """Test YoutubeApiBase URL and header construction."""

    def test_url_construction(self) -> None:
        """Test that URL is constructed with correct endpoint and params."""
        # We need to mock GoogleApiSecret for this test
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = _MockYoutubeDatafeed()
            url = datafeed.url()

            assert url.startswith("https://www.googleapis.com/youtube/v3/videos?")
            assert "part=snippet" in url
            assert "id=test_video_id" in url
            # API key should NOT be in URL
            assert "key=" not in url

    def test_headers_contain_api_key(self) -> None:
        """Test that headers contain the API key."""
        with mock.patch.object(
            GoogleApiSecret, "secret_key", return_value="test_api_key"
        ):
            datafeed = _MockYoutubeDatafeed()
            headers = datafeed.headers()

            assert headers == {"X-goog-api-key": "test_api_key"}

    def test_missing_api_key_raises_error(self) -> None:
        """Test that missing API key raises ValueError."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value=None):
            with pytest.raises(ValueError, match="No Google API key"):
                _MockYoutubeDatafeed()

    def test_base_url_constant(self) -> None:
        """Test that base URL is properly set."""
        assert YoutubeApiBase.BASE_URL == "https://www.googleapis.com/youtube/v3"
