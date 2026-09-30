from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.queries.event_query import (
    CmpDivisionsInYearQuery,
    EventQuery,
    RegionalEventsQuery,
)


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


def test_regional_events_query() -> None:
    regional = Event(
        id="2020reg",
        event_short="reg",
        year=2020,
        event_type_enum=EventType.REGIONAL,
    )
    regional.put()
    Event(
        id="2019reg",
        event_short="reg",
        year=2019,
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020dist",
        event_short="dist",
        year=2020,
        event_type_enum=EventType.DISTRICT,
    ).put()

    assert RegionalEventsQuery(year=2020).fetch() == [regional]


def test_cmp_divisions_in_year_query() -> None:
    division = Event(
        id="2020div",
        event_short="div",
        year=2020,
        event_type_enum=EventType.CMP_DIVISION,
    )
    division.put()
    Event(
        id="2020cmp",
        event_short="cmp",
        year=2020,
        event_type_enum=EventType.CMP_FINALS,
    ).put()

    assert CmpDivisionsInYearQuery(year=2020).fetch() == [division]
