import datetime
import json
from typing import Dict
from urllib.parse import urlparse

import pytest
import requests
import requests_mock
import six
from freezegun import freeze_time
from google.appengine.ext import deferred, ndb, testbed
from pyre_extensions import none_throws

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast
from backend.common.sitevars.forced_live_events import ForcedLiveEvents
from backend.common.sitevars.gameday_special_webcasts import (
    ContentType as TSpecialWebcasts,
    GamedaySpecialWebcasts,
    WebcastType as TSpecialWebcast,
)


class InMemoryRealtimeDb:
    """
    A very naive implementation of the firebase realtime db's REST API
    Since the firebase_admin SDK uses requests internally, we can hook this up
    https://firebase.google.com/docs/reference/rest/database
    """

    # a map of path -> data
    data: Dict[str, bytes]

    def __init__(self) -> None:
        self.data = {}

    def __call__(self, request: requests.models.PreparedRequest) -> requests.Response:
        url_parts = urlparse(none_throws(request.url))
        if request.method == "GET":
            data = self.data.get(url_parts.path)
            if data is None:
                return self._make_response(404, b"not found")
            return self._make_response(200, data)
        elif request.method == "PUT":
            body = six.ensure_binary(none_throws(request.body))
            self.data[url_parts.path] = body
            return self._make_response(200, body)

        return self._make_response(400, f"not implemented {request.method}".encode())

    def _make_response(self, status: int, data: bytes) -> requests.Response:
        resp = requests.Response()
        resp.status_code = status
        resp._content = data
        return resp


@pytest.fixture(autouse=True)
def auto_add_stubs(
    ndb_stub, requests_mock: requests_mock.Mocker, monkeypatch: pytest.MonkeyPatch
) -> None:
    # firebase_admin uses `requests` internally
    monkeypatch.setenv("FIREBASE_DATABASE_EMULATOR_HOST", "localhost:9070")

    requests_mock.add_matcher(InMemoryRealtimeDb())


def drain_deferred(taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub) -> None:
    for task in taskqueue_stub.get_filtered_tasks(queue_names="firebase"):
        deferred.run(task.payload)


def test_update_live_events_none(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    assert FirebasePusher._get_reference("live_events").get() == "{}"
    assert FirebasePusher._get_reference("special_webcasts").get() == "[]"


@freeze_time("2020-04-01")
def test_update_live_event(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2020, 4, 1),
        end_date=datetime.datetime(2020, 4, 1),
        name="Test Event",
        short_name="Test",
    ).put()

    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    expected = {
        "2020nyny": {
            "key": "2020nyny",
            "name": "Test Event",
            "short_name": "Test",
            "webcasts": [],
        }
    }
    assert json.loads(FirebasePusher._get_reference("live_events").get()) == expected


@freeze_time("2020-04-01")
def test_update_live_event_with_webcast(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2020, 4, 1),
        end_date=datetime.datetime(2020, 4, 1),
        name="Test Event",
        short_name="Test",
        webcast_json=json.dumps(
            [Webcast(type=WebcastType.TWITCH, channel="tbagameday")]
        ),
    ).put()

    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    expected = {
        "2020nyny": {
            "key": "2020nyny",
            "name": "Test Event",
            "short_name": "Test",
            "webcasts": [
                {
                    "type": "twitch",
                    "channel": "tbagameday",
                    "status": "unknown",
                    "stream_title": None,
                    "viewer_count": None,
                }
            ],
        }
    }
    assert json.loads(FirebasePusher._get_reference("live_events").get()) == expected


@freeze_time("2020-04-01")
def test_update_live_district_event(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2020, 4, 1),
        end_date=datetime.datetime(2020, 4, 1),
        name="Test Event",
        short_name="Test",
        district_key=ndb.Key(District, "2020ne"),
    ).put()

    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    expected = {
        "2020nyny": {
            "key": "2020nyny",
            "name": "Test Event",
            "short_name": "[NE] Test",
            "webcasts": [],
        }
    }
    assert json.loads(FirebasePusher._get_reference("live_events").get()) == expected


@freeze_time("2020-04-01")
def test_update_live_event_forced(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2020, 5, 1),
        end_date=datetime.datetime(2020, 5, 1),
        name="Test Event",
        short_name="Test",
    ).put()

    ForcedLiveEvents.put(["2020nyny"])

    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    expected = {
        "2020nyny": {
            "key": "2020nyny",
            "name": "Test Event",
            "short_name": "Test",
            "webcasts": [],
        }
    }
    assert json.loads(FirebasePusher._get_reference("live_events").get()) == expected


@freeze_time("2020-04-01")
def test_update_live_event_forced_with_webcast(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2020, 5, 1),
        end_date=datetime.datetime(2020, 5, 1),
        name="Test Event",
        short_name="Test",
        webcast_json=json.dumps(
            [Webcast(type=WebcastType.TWITCH, channel="tbagameday")]
        ),
    ).put()

    ForcedLiveEvents.put(["2020nyny"])

    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    expected = {
        "2020nyny": {
            "key": "2020nyny",
            "name": "Test Event",
            "short_name": "Test",
            "webcasts": [
                {
                    "type": "twitch",
                    "channel": "tbagameday",
                    "status": "unknown",
                    "stream_title": None,
                    "viewer_count": None,
                }
            ],
        }
    }
    assert json.loads(FirebasePusher._get_reference("live_events").get()) == expected


def test_update_special_webcast(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    data: TSpecialWebcasts = {
        "default_chat": "tbagameday",
        "webcasts": [
            TSpecialWebcast(
                type=WebcastType.TWITCH,
                channel="tbagameday",
                name="TBA Gameday",
            )
        ],
        "aliases": {},
    }
    GamedaySpecialWebcasts.put(data)

    FirebasePusher.update_live_events()
    drain_deferred(taskqueue_stub)

    expected = [
        TSpecialWebcast(
            type=WebcastType.TWITCH,
            channel="tbagameday",
            name="TBA Gameday",
            status=WebcastStatus.UNKNOWN,
            stream_title=None,
            viewer_count=None,
        )
    ]
    assert (
        json.loads(FirebasePusher._get_reference("special_webcasts").get()) == expected
    )
