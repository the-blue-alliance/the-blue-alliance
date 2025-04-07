import json
from datetime import datetime
from typing import Optional
from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.helpers.special_webcast_helper import SpecialWebcastHelper
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast, WebcastOnlineStatus
from backend.common.sitevars.forced_live_events import ForcedLiveEvents
from backend.common.sitevars.gameday_special_webcasts import (
    WebcastType as TSpecialWebcast,
)
from backend.tasks_io.helpers.live_event_helper import LiveEventHelper
from backend.tasks_io.helpers.webcast_online_helper import WebcastOnlineHelper


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


class WebcastStatusMock:
    def __init__(self, status: WebcastOnlineStatus) -> None:
        self.status = status

    def __call__(self, webcast: Webcast) -> InstantFuture[None]:
        webcast.update(self.status)
        return InstantFuture(None)


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
@patch.object(WebcastOnlineHelper, "add_online_status_async")
def test_current_event_webcasts_no_live_info(status_fetch_mock: Mock) -> None:
    create_event(webcast_date=None)
    status_fetch_mock.side_effect = WebcastStatusMock(
        WebcastOnlineStatus(
            status=WebcastStatus.UNKNOWN, stream_title=None, viewer_count=None
        )
    )

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
@patch.object(WebcastOnlineHelper, "add_online_status_async")
def test_current_event_webcasts_with_live_info(status_fetch_mock: Mock) -> None:
    create_event(webcast_date=None)
    status_fetch_mock.side_effect = WebcastStatusMock(
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
        )
    )

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
@patch.object(WebcastOnlineHelper, "add_online_status_async")
def test_current_event_webcasts_with_live_info_current_date(
    status_fetch_mock: Mock,
) -> None:
    create_event(webcast_date=datetime(2025, 4, 1))
    status_fetch_mock.side_effect = WebcastStatusMock(
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
        )
    )

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
@patch.object(WebcastOnlineHelper, "add_online_status_async")
def test_current_event_webcasts_with_live_info_different_date(
    status_fetch_mock: Mock,
) -> None:
    create_event(webcast_date=datetime(2025, 4, 1))
    status_fetch_mock.side_effect = WebcastStatusMock(
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
        )
    )

    live_events, _ = LiveEventHelper.get_live_events_with_current_webcasts()

    assert len(live_events) == 1
    assert "2025test" in live_events

    webcasts = live_events["2025test"].webcast
    assert webcasts == []


@patch.object(WebcastOnlineHelper, "add_online_status_async")
def test_forced_live_events(status_fetch_mock: Mock) -> None:
    create_event(webcast_date=None)
    ForcedLiveEvents.put(["2025test"])
    status_fetch_mock.side_effect = WebcastStatusMock(
        WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="Test stream",
            viewer_count=100,
        )
    )

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
def test_special_webcasts(special_webcast_mock: Mock) -> None:
    w = TSpecialWebcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        key_name="special",
        name="Special Webcast",
    )
    special_webcast_mock.return_value = InstantFuture([w])

    _, special_webcasts = LiveEventHelper.get_live_events_with_current_webcasts()
    assert special_webcasts == [w]
