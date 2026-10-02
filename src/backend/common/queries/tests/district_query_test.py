from google.appengine.ext import ndb

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.team import Team
from backend.common.queries.district_query import (
    AllDistrictTeamsQuery,
    DistrictAbbreviationQuery,
    DistrictQuery,
)


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


def test_all_district_teams() -> None:
    dt = DistrictTeam(
        id="2019ne_frc254",
        team=ndb.Key(Team, "frc254"),
        year=2019,
        district_key=ndb.Key(District, "2019ne"),
    )
    dt.put()

    assert AllDistrictTeamsQuery().fetch() == [dt]


def test_district_abbreviation_query_includes_renamed_codes() -> None:
    d2019 = District(id="2019fma", year=2019, abbreviation="fma")
    d2019.put()
    d2018 = District(id="2018mar", year=2018, abbreviation="mar")
    d2018.put()
    District(id="2019ne", year=2019, abbreviation="ne").put()

    districts = DistrictAbbreviationQuery(abbreviation="fma").fetch()
    assert districts == [d2018, d2019]
