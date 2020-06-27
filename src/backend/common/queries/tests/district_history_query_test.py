from backend.common.models.district import District
from backend.common.models.keys import DistrictAbbreviation
from backend.common.queries.district_query import DistrictHistoryQuery


def preseed_district(year: int, abbrev: DistrictAbbreviation) -> None:
    d = District(id=f"{year}{abbrev}", year=year, abbreviation=abbrev,)
    d.put()


def test_no_districts() -> None:
    districts = DistrictHistoryQuery(abbreviation="ne").fetch()
    assert districts == []


def test_district_history() -> None:
    preseed_district(2019, "fim")
    preseed_district(2019, "ne")
    preseed_district(2018, "ne")

    districts = DistrictHistoryQuery(abbreviation="ne").fetch()
    assert len(districts) == 2


def test_district_history_across_rename() -> None:
    preseed_district(2019, "fma")
    preseed_district(2018, "mar")

    districts_fma = DistrictHistoryQuery(abbreviation="fma").fetch()
    districts_mar = DistrictHistoryQuery(abbreviation="mar").fetch()

    assert len(districts_fma) == 2
    assert len(districts_mar) == 2
