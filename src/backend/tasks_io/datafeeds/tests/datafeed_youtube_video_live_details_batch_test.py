from unittest import mock
from urllib.parse import parse_qs, urlparse

from backend.common.datafeeds.datafeed_youtube import (
    YoutubeVideoLiveDetailsBatchDatafeed,
)
from backend.common.datafeeds.parsers.youtube.youtube_video_live_details_batch_parser import (
    YoutubeVideoLiveDetailsBatchParser,
)
from backend.common.sitevars.google_api_secret import GoogleApiSecret


class TestYoutubeVideoLiveDetailsBatchDatafeed:
    def test_endpoint(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoLiveDetailsBatchDatafeed(["video1"])
            assert datafeed.endpoint() == "videos"

    def test_url_params(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoLiveDetailsBatchDatafeed(["video1", "video2"])
            params = datafeed.url_params()

            assert params["part"] == "liveStreamingDetails"
            assert params["id"] == "video1,video2"

    def test_url_and_headers(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoLiveDetailsBatchDatafeed(["video1", "video2"])
            parsed = urlparse(datafeed.url())
            query = parse_qs(parsed.query)

            assert parsed.path == "/youtube/v3/videos"
            assert query["part"] == ["liveStreamingDetails"]
            assert query["id"] == ["video1,video2"]
            assert "key" not in query
            assert datafeed.headers() == {"X-goog-api-key": "test_key"}

    def test_parser(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoLiveDetailsBatchDatafeed(["video1", "video2"])
            parser = datafeed.parser()

            assert isinstance(parser, YoutubeVideoLiveDetailsBatchParser)


class TestYoutubeVideoLiveDetailsBatchParser:
    def test_parse_live_details(self) -> None:
        parser = YoutubeVideoLiveDetailsBatchParser(["video1", "video2", "video3"])
        response = {
            "items": [
                {
                    "id": "video1",
                    "liveStreamingDetails": {
                        "scheduledStartTime": "2026-03-15T18:00:00Z",
                    },
                },
                {
                    "id": "video2",
                    "liveStreamingDetails": {
                        "scheduledStartTime": "2026-03-16T19:00:00Z",
                    },
                },
            ]
        }

        result = parser.parse(response)

        assert result["video1"] == "2026-03-15T18:00:00Z"
        assert result["video2"] == "2026-03-16T19:00:00Z"
        assert result["video3"] == ""
