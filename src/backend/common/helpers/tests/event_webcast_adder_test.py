import json

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast

TWITCH = Webcast(type=WebcastType.TWITCH, channel="firstinspires")
YOUTUBE = Webcast(type=WebcastType.YOUTUBE, channel="abc123")


def _event(webcasts=None) -> Event:
    event = Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        webcast_json=json.dumps(webcasts) if webcasts is not None else None,
    )
    event.put()
    return event


def test_add_webcast_to_empty_event(ndb_stub, taskqueue_stub) -> None:
    event = EventWebcastAdder.add_webcast(_event(), TWITCH)
    assert event.webcast == [TWITCH]


def test_add_webcast_list_replaces(ndb_stub, taskqueue_stub) -> None:
    event = EventWebcastAdder.add_webcast(_event([TWITCH]), [YOUTUBE], update=False)
    assert event.webcast == [YOUTUBE]


def test_add_webcast_appends(ndb_stub, taskqueue_stub) -> None:
    event = EventWebcastAdder.add_webcast(_event([TWITCH]), YOUTUBE)
    assert event.webcast == [TWITCH, YOUTUBE]


def test_add_existing_webcast_is_noop(ndb_stub) -> None:
    event = _event([TWITCH])
    assert EventWebcastAdder.add_webcast(event, TWITCH) is event
    assert event.webcast == [TWITCH]


def test_remove_webcast(ndb_stub, taskqueue_stub) -> None:
    event = EventWebcastAdder.remove_webcast(
        _event([TWITCH, YOUTUBE]), 0, WebcastType.TWITCH, "firstinspires", None
    )
    assert event is not None
    assert event.webcast == [YOUTUBE]


def test_remove_webcast_bad_index(ndb_stub) -> None:
    assert (
        EventWebcastAdder.remove_webcast(
            _event([TWITCH]), 3, WebcastType.TWITCH, "firstinspires", None
        )
        is None
    )
    assert (
        EventWebcastAdder.remove_webcast(
            _event(), 0, WebcastType.TWITCH, "firstinspires", None
        )
        is None
    )


def test_remove_webcast_mismatch(ndb_stub) -> None:
    assert (
        EventWebcastAdder.remove_webcast(
            _event([TWITCH]), 0, WebcastType.TWITCH, "someone_else", None
        )
        is None
    )
