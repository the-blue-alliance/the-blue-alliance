from unittest.mock import patch

import pytest
from google.appengine.ext import testbed

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.models.webcast import Webcast
from backend.common.sitevars.google_api_secret import (
    ContentType as GoogleAPISecretContentType,
    GoogleApiSecret,
)
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_youtube_batch import YoutubeWebcastStatusBatch


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture(autouse=True)
def auto_add_urlfetch_stub(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    pass


@pytest.fixture(autouse=True)
def youtube_api_secrets() -> None:
    GoogleApiSecret.put(GoogleAPISecretContentType(api_key="test_api_key"))


def test_youtube_batch_successful_single_video() -> None:
    """Test successful batch fetch with a single YouTube video."""
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )

    df = YoutubeWebcastStatusBatch([webcast])

    with patch.object(df, "_fetch") as mock_fetch:
        mock_fetch.return_value = InstantFuture(
            URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/videos",
                200,
                '{"items": [{"id": "tbagameday", "snippet": {"liveBroadcastContent": "none", "title": "Test"}}]}',
            )
        )
        result = df.fetch_async().get_result()

    assert result is not None
    assert "tbagameday" in result
    assert result["tbagameday"]["status"] == WebcastStatus.OFFLINE


def test_youtube_batch_successful_multiple_videos() -> None:
    """Test successful batch fetch with multiple YouTube videos."""
    webcasts = [
        Webcast(type=WebcastType.YOUTUBE, channel="tbagameday"),
        Webcast(type=WebcastType.YOUTUBE, channel="tbatube"),
        Webcast(type=WebcastType.YOUTUBE, channel="tbastream"),
    ]

    df = YoutubeWebcastStatusBatch(webcasts)

    with patch.object(df, "_fetch") as mock_fetch:
        mock_fetch.return_value = InstantFuture(
            URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/videos",
                200,
                '{"items": [{"id": "tbagameday", "snippet": {"liveBroadcastContent": "none", "title": "Test 1"}}, {"id": "tbatube", "snippet": {"liveBroadcastContent": "live", "title": "Test 2"}}, {"id": "tbastream", "snippet": {"liveBroadcastContent": "none", "title": "Test 3"}}]}',
            )
        )
        result = df.fetch_async().get_result()

    assert result is not None
    assert len(result) == 3
    assert "tbagameday" in result
    assert "tbatube" in result
    assert "tbastream" in result


def test_youtube_batch_403_forbidden() -> None:
    """Test that 403 Forbidden errors are handled gracefully.

    When YouTube API returns 403 Forbidden (access denied), the datafeed
    should return None instead of crashing. This allows the caller
    (WebcastOnlineHelper) to gracefully handle it.
    """
    webcasts = [
        Webcast(type=WebcastType.YOUTUBE, channel="tbagameday"),
        Webcast(type=WebcastType.YOUTUBE, channel="tbatube"),
    ]

    df = YoutubeWebcastStatusBatch(webcasts)

    with patch.object(df, "_fetch") as mock_fetch:
        mock_fetch.return_value = InstantFuture(
            URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/videos",
                403,
                "Forbidden",
            )
        )
        result = df.fetch_async().get_result()

    # Should return None when API access is forbidden
    assert result is None


def test_youtube_batch_api_error_5xx() -> None:
    """Test that 5xx server errors are handled gracefully."""
    webcasts = [
        Webcast(type=WebcastType.YOUTUBE, channel="tbagameday"),
    ]

    df = YoutubeWebcastStatusBatch(webcasts)

    with patch.object(df, "_fetch") as mock_fetch:
        mock_fetch.return_value = InstantFuture(
            URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/videos",
                500,
                "Internal Server Error",
            )
        )
        result = df.fetch_async().get_result()

    # Should return None when API has internal error
    assert result is None


def test_youtube_batch_url_construction() -> None:
    """Test that the batch URL is correctly constructed with video IDs."""
    webcasts = [
        Webcast(type=WebcastType.YOUTUBE, channel="video1"),
        Webcast(type=WebcastType.YOUTUBE, channel="video2"),
        Webcast(type=WebcastType.YOUTUBE, channel="video3"),
    ]

    df = YoutubeWebcastStatusBatch(webcasts)
    url = df.url()

    # Should include all video IDs in the URL
    assert "video1" in url
    assert "video2" in url
    assert "video3" in url
    assert "googleapis.com/youtube/v3/videos" in url
    assert "part=snippet,liveStreamingDetails" in url


def test_youtube_batch_headers_include_api_key() -> None:
    """Test that the API key is included in request headers."""
    webcasts = [Webcast(type=WebcastType.YOUTUBE, channel="tbagameday")]

    df = YoutubeWebcastStatusBatch(webcasts)
    headers = df.headers()

    assert "X-goog-api-key" in headers
    assert headers["X-goog-api-key"] == "test_api_key"


def test_youtube_batch_non_youtube_webcast_raises_error() -> None:
    """Test that non-YouTube webcasts raise an error."""
    webcast_html5 = Webcast(
        type=WebcastType.HTML5,
        channel="http://example.com/stream.m4v",
    )

    with pytest.raises(ValueError, match="is not youtube"):
        YoutubeWebcastStatusBatch([webcast_html5])


def test_youtube_batch_mixed_types_raises_error() -> None:
    """Test that mixing YouTube and non-YouTube webcasts raises an error."""
    webcasts = [
        Webcast(type=WebcastType.YOUTUBE, channel="tbagameday"),
        Webcast(type=WebcastType.TWITCH, channel="tbagameday"),
    ]

    with pytest.raises(ValueError, match="is not youtube"):
        YoutubeWebcastStatusBatch(webcasts)


def test_youtube_batch_empty_list() -> None:
    """Test behavior with an empty webcast list."""
    df = YoutubeWebcastStatusBatch([])

    # Should still construct valid URL even with empty list
    url = df.url()
    assert "googleapis.com/youtube/v3/videos" in url
