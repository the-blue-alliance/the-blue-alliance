import json
from datetime import datetime
from typing import Optional
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.helpers.special_webcast_helper import SpecialWebcastHelper
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast
from backend.common.sitevars.forced_live_events import ForcedLiveEvents
from backend.common.sitevars.gameday_special_webcasts import (
    WebcastType as TSpecialWebcast,
)
from backend.tasks_io.helpers.live_event_helper import LiveEventHelper


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


def create_event(webcast_date: Optional[datetime]) -> None:
    w = Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
    )
    if webcast_date:
        w["date"] = webcast_date.strftime("%Y-%m-%d")

    e = Event(
        id="2025test",
        year=2025,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2025, 4, 1),
        end_date=datetime(2025, 4, 2),
        webcast_json=json.dumps([w]),
    )
    e.put()


@freeze_time("2025-04-01")
def test_current_event_webcasts_no_live_info() -> None:
    create_event(webcast_date=None)

    live_events, _ = LiveEventHelper.get_live_events_with_current_webcasts()

    assert len(live_events) == 1
    assert "2025test" in live_events

    webcasts = live_events["2025test"].webcast
    assert webcasts == [
        Webcast(
            type=WebcastType.YOUTUBE,
            channel="abc123",
            status=WebcastStatus.UNKNOWN,
            stream_title=None,
            viewer_count=None,
        )
    ]


@freeze_time("2025-04-01")
def test_current_event_webcasts_with_live_info() -> None:
    create_event(webcast_date=None)
    w = Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )
    WebcastOnlineStatusMemcache(w).put(w)

    live_events, _ = LiveEventHelper.get_live_events_with_current_webcasts()

    assert len(live_events) == 1
    assert "2025test" in live_events

    webcasts = live_events["2025test"].webcast
    assert webcasts == [
        Webcast(
            type=WebcastType.YOUTUBE,
            channel="abc123",
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
        )
    ]


@freeze_time("2025-04-01")
def test_current_event_webcasts_with_live_info_current_date() -> None:
    create_event(webcast_date=datetime(2025, 4, 1))
    w = Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )
    WebcastOnlineStatusMemcache(w).put(w)

    live_events, _ = LiveEventHelper.get_live_events_with_current_webcasts()

    assert len(live_events) == 1
    assert "2025test" in live_events

    webcasts = live_events["2025test"].webcast
    assert webcasts == [
        Webcast(
            type=WebcastType.YOUTUBE,
            channel="abc123",
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
            date="2025-04-01",
        )
    ]


@freeze_time("2025-04-02")
def test_current_event_webcasts_with_live_info_different_date() -> None:
    create_event(webcast_date=datetime(2025, 4, 1))
    w = Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )
    WebcastOnlineStatusMemcache(w).put(w)

    live_events, _ = LiveEventHelper.get_live_events_with_current_webcasts()

    assert len(live_events) == 1
    assert "2025test" in live_events

    webcasts = live_events["2025test"].webcast
    assert webcasts == []


def test_forced_live_events() -> None:
    create_event(webcast_date=None)
    ForcedLiveEvents.put(["2025test"])

    w = Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )
    WebcastOnlineStatusMemcache(w).put(w)

    live_events, _ = LiveEventHelper.get_live_events_with_current_webcasts()

    assert len(live_events) == 1
    assert "2025test" in live_events

    webcasts = live_events["2025test"].webcast
    assert webcasts == [
        Webcast(
            type=WebcastType.YOUTUBE,
            channel="abc123",
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
        )
    ]


@patch.object(SpecialWebcastHelper, "get_special_webcasts_with_online_status_async")
def test_special_webcasts(mock) -> None:
    w = TSpecialWebcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        key_name="special",
        name="Special Webcast",
    )
    mock.return_value = InstantFuture([w])

    _, special_webcasts = LiveEventHelper.get_live_events_with_current_webcasts()
    assert special_webcasts == [w]
