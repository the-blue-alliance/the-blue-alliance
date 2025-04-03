import json
from urllib.parse import urlparse

import pytest

from google.appengine.ext import testbed

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.webcast_online_helper import WebcastOnlineHelper
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.webcast import Webcast
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.sitevars.twitch_secrets import TwitchSecrets


@pytest.fixture(autouse=True)
def add_gae_testbed(memcache_stub, ndb_stub):
    pass


@pytest.fixture
def enable_update_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UPDATE_WEBCAST_ONLINE_STATUS", "true")


@pytest.fixture
def set_twitch_secrets(ndb_stub) -> None:
    TwitchSecrets.put({"client_id": "tba", "client_secret": "secret"})


@pytest.fixture
def set_youtube_secrets(ndb_stub) -> None:
    GoogleApiSecret.put({"api_key": "secret"})


class MockTwitchAuth:
    def __call__(self, url, payload, method, headers, request, response, **kwargs):
        response.StatusCode = 200
        response.Content = json.dumps({"access_token": "123testtoken"}).encode()


class MockTwitchApi:
    def __init__(self, online=True, fail=False, throw=False) -> None:
        self.online = online
        self.fail = fail
        self.throw = throw

    def __call__(self, url, payload, method, headers, request, response, **kwargs):
        if self.throw:
            raise Exception
        response.StatusCode = 200 if not self.fail else 500
        if self.online:
            response.Content = json.dumps(
                {
                    "data": [
                        {
                            "id": "41375541868",
                            "user_id": "459331509",
                            "user_login": "tbagameday",
                            "user_name": "tbagameday",
                            "type": "live",
                            "title": "A Stream",
                            "viewer_count": 1337,
                            "started_at": "2021-03-10T15:04:21Z",
                        },
                    ],
                }
            ).encode()
        else:
            response.Content = json.dumps({"data": []}).encode()


class MockYoutubeApi:
    def __init__(
        self, online=True, status="live", viewers=None, fail=False, throw=False
    ) -> None:
        self.online = online
        self.status = status
        self.viewers = viewers
        self.fail = fail
        self.throw = throw

    def __call__(self, url, payload, method, headers, request, response, **kwargs):
        if self.throw:
            raise Exception
        response.StatusCode = 200 if not self.fail else 500
        if self.online:
            live_details = {
                "actualStartTime": "2025-03-29T14:33:11Z",
                "actualEndTime": "2025-03-29T22:04:00Z",
                "scheduledStartTime": "2025-03-29T14:30:00Z",
            }
            if self.status == "live":
                live_details["concurrentViewers"] = f"{self.viewers}"
            response.Content = json.dumps(
                {
                    "items": [
                        {
                            "snippet": {
                                "liveBroadcastContent": self.status,
                                "title": "A Stream",
                            },
                            "liveStreamingDetails": live_details,
                        }
                    ]
                }
            ).encode()
        else:
            response.Content = json.dumps({"items": []}).encode()


class MockUStreamApi:
    def __init__(self, online=True, status="live", fail=False, throw=False) -> None:
        self.online = online
        self.status = status
        self.fail = fail
        self.throw = throw

    def __call__(self, url, payload, method, headers, request, response, **kwargs):
        if self.throw:
            raise Exception
        response.StatusCode = 200 if not self.fail else 500
        if self.online:
            response.Content = json.dumps(
                {
                    "channel": {
                        "status": self.status,
                        "title": "A Stream",
                    }
                }
            ).encode()
        else:
            response.Content = json.dumps({"channel": {}}).encode()


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


def test_add_online_status_twitch_no_secrets(
    gae_testbed: testbed.Testbed, enable_update_status
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (lambda url: urlparse(url).netloc == "id.twitch.tv", MockTwitchAuth()),
            (lambda url: urlparse(url).netloc == "api.twitch.tv", MockTwitchApi()),
        ]
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_twitch_http_failue(
    gae_testbed: testbed.Testbed, enable_update_status, set_twitch_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (lambda url: urlparse(url).netloc == "id.twitch.tv", MockTwitchAuth()),
            (
                lambda url: urlparse(url).netloc == "api.twitch.tv",
                MockTwitchApi(fail=True),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_twitch_http_error(
    gae_testbed: testbed.Testbed, enable_update_status, set_twitch_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (lambda url: urlparse(url).netloc == "id.twitch.tv", MockTwitchAuth()),
            (
                lambda url: urlparse(url).netloc == "api.twitch.tv",
                MockTwitchApi(throw=True),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_twitch(
    gae_testbed: testbed.Testbed, enable_update_status, set_twitch_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (lambda url: urlparse(url).netloc == "id.twitch.tv", MockTwitchAuth()),
            (lambda url: urlparse(url).netloc == "api.twitch.tv", MockTwitchApi()),
        ]
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] == 1337


def test_add_online_status_twitch_offline(
    gae_testbed: testbed.Testbed, enable_update_status, set_twitch_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (lambda url: urlparse(url).netloc == "id.twitch.tv", MockTwitchAuth()),
            (
                lambda url: urlparse(url).netloc == "api.twitch.tv",
                MockTwitchApi(online=False),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.OFFLINE


def test_add_online_status_youtube_no_secrets(
    gae_testbed: testbed.Testbed, enable_update_status
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "www.googleapis.com",
                MockYoutubeApi(),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_youtube_http_failure(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "www.googleapis.com",
                MockYoutubeApi(fail=True),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_youtube_http_error(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "www.googleapis.com",
                MockYoutubeApi(throw=True),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_youtube(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "www.googleapis.com",
                MockYoutubeApi(viewers=100),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] == 100


def test_add_online_status_youtube_stream_upcoming(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "www.googleapis.com",
                MockYoutubeApi(status="upcoming"),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.OFFLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] is None


def test_add_online_status_youtube_no_stream(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "www.googleapis.com",
                MockYoutubeApi(online=False),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.YOUTUBE,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.OFFLINE
    assert webcast["stream_title"] is None
    assert webcast["viewer_count"] is None


def test_add_online_status_ustream_http_failure(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "api.ustream.tv",
                MockUStreamApi(fail=True),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.USTREAM,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_ustream_http_error(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "api.ustream.tv",
                MockUStreamApi(throw=True),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.USTREAM,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.UNKNOWN


def test_add_online_status_ustream(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (lambda url: urlparse(url).netloc == "api.ustream.tv", MockUStreamApi()),
        ]
    )
    webcast = Webcast(
        type=WebcastType.USTREAM,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.ONLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] is None


def test_add_online_status_ustream_offline(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "api.ustream.tv",
                MockUStreamApi(status="offair"),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.USTREAM,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.OFFLINE
    assert webcast["stream_title"] == "A Stream"
    assert webcast["viewer_count"] is None


def test_add_online_status_ustream_no_stream(
    gae_testbed: testbed.Testbed, enable_update_status, set_youtube_secrets
) -> None:
    gae_testbed.init_urlfetch_stub(
        urlmatchers=[
            (
                lambda url: urlparse(url).netloc == "api.ustream.tv",
                MockUStreamApi(online=False),
            ),
        ]
    )
    webcast = Webcast(
        type=WebcastType.USTREAM,
        channel="tbagameday",
    )
    WebcastOnlineHelper.add_online_status([webcast])

    assert webcast["status"] == WebcastStatus.OFFLINE
    assert webcast["stream_title"] is None
    assert webcast["viewer_count"] is None
