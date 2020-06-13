from google.cloud import ndb
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.queries.event_query import EventDivisionsQuery


def preseed_event_with_divisions(year: int, n: int) -> None:
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
    Event(
        id=f"{year}test",
        event_short="test",
        year=year,
        event_type_enum=EventType.OFFSEASON,
        divisions=stored,
    ).put()


def test_no_event() -> None:
    divisions = EventDivisionsQuery(event_key="2020test").fetch()
    assert divisions == []


def test_no_divisions() -> None:
    Event(
        id="2020test",
        event_short="test",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
    ).put()
    divisions = EventDivisionsQuery(event_key="2020test").fetch()
    assert divisions == []


def test_with_divisions() -> None:
    preseed_event_with_divisions(year=2020, n=5)
    divisions = EventDivisionsQuery(event_key="2020test").fetch()
    assert len(divisions) == 5
