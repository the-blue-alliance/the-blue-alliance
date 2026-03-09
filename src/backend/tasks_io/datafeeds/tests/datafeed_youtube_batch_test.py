from unittest import mock
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.models.webcast import Webcast
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_youtube import YoutubeWebcastStatusBatch
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_status_batch_parser import (
    YoutubeStreamStatusBatchParser,
)


class TestYoutubeWebcastStatusBatch:
    def test_requires_youtube_webcasts(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            with pytest.raises(ValueError, match="is not youtube"):
                YoutubeWebcastStatusBatch(
                    [Webcast(type=WebcastType.TWITCH, channel="channel")]
                )

    def test_url_params_and_headers(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            batch = YoutubeWebcastStatusBatch(
                [
                    Webcast(type=WebcastType.YOUTUBE, channel="video1"),
                    Webcast(type=WebcastType.YOUTUBE, channel="video2"),
                ]
            )

            parsed = urlparse(batch.url())
            query = parse_qs(parsed.query)

            assert parsed.path == "/youtube/v3/videos"
            assert query["part"] == ["snippet,liveStreamingDetails"]
            assert query["id"] == ["video1,video2"]
            assert "key" not in query
            assert batch.headers() == {"X-goog-api-key": "test_key"}

    def test_parser(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            batch = YoutubeWebcastStatusBatch(
                [Webcast(type=WebcastType.YOUTUBE, channel="video1")]
            )
            parser = batch.parser()
            assert isinstance(parser, YoutubeStreamStatusBatchParser)

    def test_403_forbidden_returns_none(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            batch = YoutubeWebcastStatusBatch(
                [Webcast(type=WebcastType.YOUTUBE, channel="video1")]
            )

            with patch.object(batch, "_fetch") as mock_fetch:
                mock_fetch.return_value = InstantFuture(
                    URLFetchResult.mock_for_content(
                        "https://www.googleapis.com/youtube/v3/videos",
                        403,
                        "Forbidden",
                    )
                )
                result = batch.fetch_async().get_result()

        assert result is None

    def test_500_error_returns_none(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            batch = YoutubeWebcastStatusBatch(
                [Webcast(type=WebcastType.YOUTUBE, channel="video1")]
            )

            with patch.object(batch, "_fetch") as mock_fetch:
                mock_fetch.return_value = InstantFuture(
                    URLFetchResult.mock_for_content(
                        "https://www.googleapis.com/youtube/v3/videos",
                        500,
                        "Internal Server Error",
                    )
                )
                result = batch.fetch_async().get_result()

        assert result is None

    def test_parse_success_response(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            batch = YoutubeWebcastStatusBatch(
                [Webcast(type=WebcastType.YOUTUBE, channel="tbagameday")]
            )

            with patch.object(batch, "_fetch") as mock_fetch:
                mock_fetch.return_value = InstantFuture(
                    URLFetchResult.mock_for_content(
                        "https://www.googleapis.com/youtube/v3/videos",
                        200,
                        '{"items": [{"id": "tbagameday", "snippet": {"liveBroadcastContent": "none", "title": "Test"}}]}',
                    )
                )
                result = batch.fetch_async().get_result()

        assert result is not None
        assert result["tbagameday"]["status"] == WebcastStatus.OFFLINE
