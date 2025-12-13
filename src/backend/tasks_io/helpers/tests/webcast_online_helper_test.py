from datetime import datetime
from unittest import mock

import pytest
from freezegun import freeze_time
from pyre_extensions import none_throws

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.memcache_models.twitch_oauth_token_memcache import (
    TwitchOauthTokenMemcache,
)
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.twitch_access_token import TwitchAccessToken
from backend.common.models.webcast import Webcast, WebcastOnlineStatus
from backend.common.sitevars.google_api_secret import (
    ContentType as GoogleAPISecretContentType,
    GoogleApiSecret,
)
from backend.common.sitevars.twitch_secrets import (
    ContentType as TwitchSecretsContent,
    TwitchSecrets,
)
from backend.tasks_io.datafeeds.datafeed_twitch import (
    TwitchGetAccessToken,
    TwitchWebcastStatus,
)
from backend.tasks_io.datafeeds.datafeed_youtube import YoutubeWebcastStatus
from backend.tasks_io.helpers.webcast_online_helper import WebcastOnlineHelper


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture(autouse=True)
def twitch_secrets(ndb_stub) -> None:
    TwitchSecrets.put(TwitchSecretsContent(client_id="test", client_secret="test"))


@pytest.fixture(autouse=True)
def youtube_api_secrets() -> None:
    GoogleApiSecret.put(GoogleAPISecretContentType(api_key="test"))


class WebcastStatusMock:
    def __init__(self, webcast: Webcast, status: WebcastOnlineStatus) -> None:
        self.webcast = webcast
        self.status = status

    def __call__(self) -> InstantFuture[None]:
        self.webcast.update(self.status)
        return InstantFuture(None)


def test_add_online_status_not_in_cache() -> None:
    webcast = Webcast(
        type=WebcastType.HTML5,
        channel="test_stream.m4v",
    )

    WebcastOnlineHelper.add_online_status([webcast])
    assert webcast.get("status") == WebcastStatus.UNKNOWN
    assert webcast.get("stream_title") is None
    assert webcast.get("viewer_count") is None

    # Check we write the updated dict back to cache
    cache_data = WebcastOnlineStatusMemcache(webcast).get()
    assert webcast == cache_data


def test_add_online_status_in_cache() -> None:
    webcast = Webcast(
        type=WebcastType.HTML5,
        channel="test_stream.m4v",
    )
    webcast_with_status = Webcast(
        type=WebcastType.HTML5,
        channel="test_stream.m4v",
        status=WebcastStatus.ONLINE,
        stream_title="A Stream",
        viewer_count=1337,
    )

    WebcastOnlineStatusMemcache(webcast).put(webcast_with_status)

    WebcastOnlineHelper.add_online_status([webcast])
    assert webcast == webcast_with_status


@mock.patch.object(YoutubeWebcastStatus, "fetch_async")
def test_add_online_status_youtube(youtube_mock: mock.Mock) -> None:
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )

    youtube_mock.side_effect = WebcastStatusMock(
        webcast,
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="A Stream",
            viewer_count=1337,
        ),
    )

    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] == 1337


@freeze_time("2025-04-01 00:00:00")
@mock.patch.object(TwitchWebcastStatus, "fetch_async")
@mock.patch.object(TwitchGetAccessToken, "fetch_async")
def test_add_online_status_twitch_with_token(
    token_mock: mock.Mock, fetch_mock: mock.Mock
) -> None:
    TwitchOauthTokenMemcache().expires(120).put(
        TwitchAccessToken(
            access_token="t",
            expires_in=14124,
            refresh_token="xyz",
            scope=[],
            token_type="bearer",
            expires_at=int(datetime(2025, 4, 1, 1, 0, 0).timestamp()),
            client_id="zzz",
        )
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )

    fetch_mock.side_effect = WebcastStatusMock(
        webcast,
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="A Stream",
            viewer_count=1337,
        ),
    )

    WebcastOnlineHelper.add_online_status([webcast])
    token_mock.assert_not_called()

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] == 1337


@freeze_time("2025-04-01 00:00:00")
@mock.patch.object(TwitchWebcastStatus, "fetch_async")
@mock.patch.object(TwitchGetAccessToken, "fetch_async")
def test_add_online_status_twitch_with_expired_token(
    token_mock: mock.Mock, fetch_mock: mock.Mock
) -> None:
    TwitchOauthTokenMemcache().expires(120).put(
        TwitchAccessToken(
            access_token="t",
            expires_in=14124,
            refresh_token="xyz",
            scope=[],
            token_type="bearer",
            expires_at=int(datetime(2025, 3, 1, 1, 0, 0).timestamp()),
            client_id="zzz",
        )
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    new_token = TwitchAccessToken(
        access_token="t2",
        expires_in=14124,
        refresh_token="xyz",
        scope=[],
        token_type="bearer",
        expires_at=int(datetime(2025, 4, 1, 1, 0, 0).timestamp()),
        client_id="zzz",
    )

    token_mock.return_value = InstantFuture(new_token)
    fetch_mock.side_effect = WebcastStatusMock(
        webcast,
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="A Stream",
            viewer_count=1337,
        ),
    )

    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] == 1337

    assert none_throws(TwitchOauthTokenMemcache().get())["access_token"] == "t2"


@freeze_time("2025-04-01 00:00:00")
@mock.patch.object(TwitchWebcastStatus, "fetch_async")
@mock.patch.object(TwitchGetAccessToken, "fetch_async")
def test_add_online_status_twitch_without_token(
    token_mock: mock.Mock, fetch_mock: mock.Mock
) -> None:
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    new_token = TwitchAccessToken(
        access_token="t2",
        expires_in=14124,
        refresh_token="xyz",
        scope=[],
        token_type="bearer",
        expires_at=int(datetime(2025, 4, 1, 1, 0, 0).timestamp()),
        client_id="zzz",
    )

    token_mock.return_value = InstantFuture(new_token)
    fetch_mock.side_effect = WebcastStatusMock(
        webcast,
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="A Stream",
            viewer_count=1337,
        ),
    )

    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] == 1337

    assert none_throws(TwitchOauthTokenMemcache().get())["access_token"] == "t2"
