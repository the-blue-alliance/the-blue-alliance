from backend.common.models.district import District
from backend.common.queries.district_query import DistrictQuery


def test_district_doesnt_exist() -> None:
    district = DistrictQuery(district_key="2019ne").fetch()
    assert district is None


def test_district_found() -> None:
    d = District(
        id="2019ne",
        year=2019,
        abbreviation="ne",
    )
    d.put()

    district = DistrictQuery(district_key="2019ne").fetch()
    assert district == d


def test_found_with_renamed_district() -> None:
    d = District(
        id="2019fma",
        year=2019,
        abbreviation="fma",
    )
    d.put()

    district = DistrictQuery(district_key="2019mar").fetch()
    assert district == d
