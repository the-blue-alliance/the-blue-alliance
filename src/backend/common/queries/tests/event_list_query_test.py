from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.queries.event_query import EventListQuery


def preseed_events(year: Year, n: int) -> None:
    stored = ndb.put_multi(
        [
            Event(
                id=f"{year}test{i}",
                event_short=f"test{i}",
                year=year,
                event_type_enum=EventType.OFFSEASON,
            )
            for i in range(n)
        ]
    )
    assert len(stored) == n


def test_no_events() -> None:
    events = EventListQuery(year=2020).fetch()
    assert events == []


def test_single_event() -> None:
    preseed_events(year=2020, n=1)
    events = EventListQuery(year=2020).fetch()
    assert len(events) == 1
    assert events[0].key_name == "2020test0"


def test_multiple_events() -> None:
    preseed_events(year=2020, n=5)
    events = EventListQuery(year=2020).fetch()
    assert len(events) == 5


def test_multiple_events_across_years() -> None:
    preseed_events(year=2020, n=5)
    preseed_events(year=2019, n=5)
    events = EventListQuery(year=2019).fetch()
    assert len(events) == 5
    for e in events:
        assert e.year == 2019
