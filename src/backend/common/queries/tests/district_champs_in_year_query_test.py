from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.queries.event_query import DistrictChampsInYearQuery


def preseed_event(year: Year, short: str, type: EventType) -> None:
    Event(
        id=f"{year}{short}", event_short=short, year=year, event_type_enum=type,
    ).put()


def test_none_found() -> None:
    dcmps = DistrictChampsInYearQuery(year=2019).fetch()
    assert dcmps == []


def test_with_dcmp() -> None:
    preseed_event(2019, "test1", EventType.DISTRICT_CMP)
    preseed_event(2019, "test2", EventType.REGIONAL)
    preseed_event(2018, "test3", EventType.DISTRICT_CMP)

    dcmps = DistrictChampsInYearQuery(year=2019).fetch()
    assert dcmps == [Event.get_by_id("2019test1")]
