from unittest import mock

import pytest

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.models.webcast import Webcast
from backend.common.sitevars.google_api_secret import (
    ContentType as GoogleAPISecretContentType,
    GoogleApiSecret,
)
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_youtube import (
    YoutubeWebcastStatus,
)
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_stauts_parser import (
    YoutubeStreamStatusParser,
)


@pytest.fixture
def youtube_api_secrets() -> None:
    GoogleApiSecret.put(GoogleAPISecretContentType(api_key="test"))


def test_init_requires_secret(ndb_stub) -> None:
    with pytest.raises(
        ValueError, match="No Google API key! Configure GoogleApiSecret sitevar"
    ):
        YoutubeWebcastStatus(Webcast(type=WebcastType.YOUTUBE, channel="abc123"))


def test_init_bad_webcast_type(ndb_stub, youtube_api_secrets) -> None:
    with pytest.raises(ValueError, match=".* is not youtube! Can't load status"):
        YoutubeWebcastStatus(Webcast(type=WebcastType.TWITCH, channel="abc123"))


@mock.patch.object(YoutubeStreamStatusParser, "parse")
@mock.patch.object(YoutubeWebcastStatus, "_urlfetch")
def test_get_online_status(
    api_mock: mock.Mock, parser_mock: mock.Mock, ndb_stub, youtube_api_secrets
) -> None:
    api_response = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet,liveStreamingDetails&id=abc123",
        200,
        "{}",
    )
    api_mock.return_value = InstantFuture(api_response)
    w = Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )
    parser_mock.return_value = w

    response = YoutubeWebcastStatus(
        Webcast(type=WebcastType.YOUTUBE, channel="abc123")
    ).fetch_async()
    assert response.get_result() == w
