from unittest import mock
from urllib.parse import parse_qs, urlparse

from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.tasks_io.datafeeds.datafeed_youtube import YoutubePlaylistItemsDatafeed
from backend.tasks_io.datafeeds.parsers.youtube.youtube_playlist_items_parser import (
    YoutubePlaylistItemsParser,
)


class TestYoutubePlaylistItemsDatafeed:
    def test_endpoint(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubePlaylistItemsDatafeed("PL_123")
            assert datafeed.endpoint() == "playlistItems"

    def test_default_url_params(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubePlaylistItemsDatafeed("PL_123")
            params = datafeed.url_params()

            assert params["part"] == "id,snippet"
            assert params["playlistId"] == "PL_123"
            assert params["maxResults"] == "50"
            assert "pageToken" not in params

    def test_page_token_url_params(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubePlaylistItemsDatafeed(
                "PL_123", max_results=25, page_token="NEXT_TOKEN"
            )
            params = datafeed.url_params()

            assert params["maxResults"] == "25"
            assert params["pageToken"] == "NEXT_TOKEN"

    def test_url(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubePlaylistItemsDatafeed("PL_123")
            parsed = urlparse(datafeed.url())
            query = parse_qs(parsed.query)

            assert parsed.path == "/youtube/v3/playlistItems"
            assert query["playlistId"] == ["PL_123"]
            assert query["part"] == ["id,snippet"]

    def test_parser(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubePlaylistItemsDatafeed("PL_123")
            parser = datafeed.parser()
            assert isinstance(parser, YoutubePlaylistItemsParser)
