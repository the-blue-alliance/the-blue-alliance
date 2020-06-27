from backend.common.models.district import District
from backend.common.queries.district_query import DistrictsInYearQuery


def test_no_districts() -> None:
    districts = DistrictsInYearQuery(year=2019).fetch()
    assert districts == []


def test_get_districts() -> None:
    d = District(id="2019ne", year=2019,)
    d.put()
    d2 = District(id="2018ne", year=2018,)
    d2.put()

    districts = DistrictsInYearQuery(year=2019).fetch()
    assert districts == [d]
