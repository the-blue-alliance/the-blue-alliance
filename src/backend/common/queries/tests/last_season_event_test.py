import datetime

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.queries.event_query import LastSeasonEventQuery


def test_last_season_event_ignores_offseason() -> None:
    Event(
        id="2020tes3",
        event_short="test 3",
        year=2020,
        end_date=datetime.datetime(2020, 8, 1, 0, 0),
        event_type_enum=EventType.OFFSEASON,
    ).put()
    last_event = LastSeasonEventQuery(year=2020).fetch()
    assert last_event is None


def test_last_season_event_one_event() -> None:
    tes1 = Event(
        id="2020tes1",
        event_short="test 1",
        year=2020,
        end_date=datetime.datetime(2020, 4, 1, 0, 0),
        event_type_enum=EventType.REGIONAL,
    )
    tes1.put()
    assert LastSeasonEventQuery(year=2020).fetch() == tes1


def test_last_season_event_two_events() -> None:
    tes1 = Event(
        id="2020tes1",
        event_short="test 1",
        year=2020,
        end_date=datetime.datetime(2020, 4, 1, 0, 0),
        event_type_enum=EventType.REGIONAL,
    )
    tes1.put()
    tes2 = Event(
        id="2020tes2",
        event_short="test 2",
        year=2020,
        end_date=datetime.datetime(2020, 4, 2, 0, 0),
        event_type_enum=EventType.DISTRICT,
    )
    tes2.put()
    assert LastSeasonEventQuery(year=2020).fetch() == tes2
