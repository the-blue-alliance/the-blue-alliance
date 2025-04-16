import json
from unittest import mock

import pytest

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.models.twitch_access_token import TwitchAccessToken
from backend.common.models.webcast import Webcast
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_twitch import TwitchWebcastStatus


def test_init_bad_webcast_type(ndb_stub) -> None:
    with pytest.raises(
        ValueError,
        match=".* is not twitch! Can't load status",
    ):
        w = Webcast(
            type=WebcastType.YOUTUBE,
            channel="abc123",
        )
        t = TwitchAccessToken(
            access_token="t",
            expires_in=14124,
            refresh_token="xyz",
            scope=[],
            token_type="bearer",
            expires_at=14124,
            client_id="zzz",
        )
        TwitchWebcastStatus(t, w)


@mock.patch.object(TwitchWebcastStatus, "_fetch")
def test_request(api_mock: mock.Mock) -> None:
    w = Webcast(
        type=WebcastType.TWITCH,
        channel="abc123",
    )
    t = TwitchAccessToken(
        access_token="t",
        expires_in=14124,
        refresh_token="xyz",
        scope=[],
        token_type="bearer",
        expires_at=14124,
        client_id="zzz",
    )
    api_data = {
        "data": [
            {
                "id": "123456789",
                "user_id": "98765",
                "user_login": "abc123",
                "user_name": "abc123",
                "type": "live",
                "title": "Hello darkness my old friend",
                "tags": [],
                "viewer_count": 78365,
                "started_at": "2021-03-10T15:04:21Z",
                "language": "en",
                "tag_ids": [],
                "is_mature": False,
            },
        ],
        "pagination": {
            "cursor": "eyJiIjp7IkN1cnNvciI6ImV5SnpJam8zT0RNMk5TNDBORFF4TlRjMU1UY3hOU3dpWkNJNlptRnNjMlVzSW5RaU9uUnlkV1Y5In0sImEiOnsiQ3Vyc29yIjoiZXlKeklqb3hOVGs0TkM0MU56RXhNekExTVRZNU1ESXNJbVFpT21aaGJITmxMQ0owSWpwMGNuVmxmUT09In19"
        },
    }
    api_response = URLFetchResult.mock_for_content(
        "https://api.twitch.tv/helix/streams?user_login=abc123",
        200,
        json.dumps(api_data),
    )
    api_mock.return_value = InstantFuture(api_response)

    df = TwitchWebcastStatus(t, w)

    result = df.fetch_async().get_result()
    expected = Webcast(
        type=WebcastType.TWITCH,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Hello darkness my old friend",
        viewer_count=78365,
    )
    assert result == expected


@mock.patch.object(TwitchWebcastStatus, "_fetch")
def test_request_no_stream(api_mock: mock.Mock) -> None:
    w = Webcast(
        type=WebcastType.TWITCH,
        channel="abc123",
    )
    t = TwitchAccessToken(
        access_token="t",
        expires_in=14124,
        refresh_token="xyz",
        scope=[],
        token_type="bearer",
        expires_at=14124,
        client_id="zzz",
    )
    api_data = {
        "data": [],
        "pagination": {},
    }
    api_response = URLFetchResult.mock_for_content(
        "https://api.twitch.tv/helix/streams?user_login=abc123",
        200,
        json.dumps(api_data),
    )
    api_mock.return_value = InstantFuture(api_response)

    df = TwitchWebcastStatus(t, w)

    result = df.fetch_async().get_result()
    expected = Webcast(
        type=WebcastType.TWITCH,
        channel="abc123",
        status=WebcastStatus.OFFLINE,
    )
    assert result == expected
