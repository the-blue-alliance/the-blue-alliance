from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.queries.event_query import DistrictCmpDivisionsInYearQuery


def preseed_event(year: Year, short: str, type: EventType) -> None:
    Event(
        id=f"{year}{short}",
        event_short=short,
        year=year,
        event_type_enum=type,
    ).put()


def test_none_found() -> None:
    divisions = DistrictCmpDivisionsInYearQuery(year=2019).fetch()
    assert divisions == []


def test_with_district_cmp_division() -> None:
    preseed_event(2019, "test1", EventType.DISTRICT_CMP_DIVISION)
    preseed_event(2019, "test2", EventType.REGIONAL)
    preseed_event(2019, "test3", EventType.DISTRICT_CMP)
    preseed_event(2018, "test4", EventType.DISTRICT_CMP_DIVISION)

    divisions = DistrictCmpDivisionsInYearQuery(year=2019).fetch()
    assert divisions == [Event.get_by_id("2019test1")]
