from typing import Optional

from google.cloud import ndb
from pyre_extensions import none_throws

from backend.common.consts.event_type import EventType
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.keys import DistrictAbbreviation, Year
from backend.common.queries.event_query import DistrictEventsQuery


def preseed_events(
    year: Year, n: int, district_abbrev: Optional[DistrictAbbreviation]
) -> None:
    event_type = EventType.DISTRICT if district_abbrev else EventType.REGIONAL
    district_key = (
        ndb.Key(District, f"{year}{district_abbrev}") if district_abbrev else None
    )
    stored = ndb.put_multi(
        [
            Event(
                id=f"{year}{district_abbrev or ''}test{i}",
                event_short=f"test{i}",
                year=year,
                event_type_enum=event_type,
                district_key=district_key,
            )
            for i in range(n)
        ]
    )
    assert len(stored) == n


def test_no_events() -> None:
    events = DistrictEventsQuery(district_key="2019ne").fetch()
    assert events == []


def test_no_events_with_districts() -> None:
    preseed_events(2019, 3, district_abbrev=None)
    events = DistrictEventsQuery(district_key="2019ne").fetch()
    print(f"{events}")
    assert events == []


def test_with_districts() -> None:
    preseed_events(2019, 3, "ne")
    preseed_events(2018, 3, "ne")
    preseed_events(2019, 3, "fim")

    events = DistrictEventsQuery(district_key="2019ne").fetch()
    assert len(events) == 3
    assert all(
        e.district_key is not None and none_throws(e.district_key).id() == "2019ne"
        for e in events
    )
