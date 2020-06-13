from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.queries.event_query import EventQuery


def test_event_not_found() -> None:
    event = EventQuery(event_key="2020asdf").fetch()
    assert event is None


def test_event_is_found() -> None:
    Event(
        id="2020test",
        event_short="test",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
    ).put()
    result = EventQuery(event_key="2020test").fetch()
    assert result is not None
    assert result.key_name == "2020test"
