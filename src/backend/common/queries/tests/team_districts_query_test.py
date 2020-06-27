from google.cloud import ndb

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.keys import DistrictKey
from backend.common.models.team import Team
from backend.common.queries.district_query import TeamDistrictsQuery


def preseed_district_team(team_number: int, district_key: DistrictKey) -> None:
    District(id=district_key, year=int(district_key[:4]),).put()

    DistrictTeam(
        id=f"{district_key}_{team_number}",
        team=ndb.Key(Team, f"frc{team_number}"),
        district_key=ndb.Key(District, district_key),
        year=int(district_key[:4]),
    ).put()


def test_no_districts() -> None:
    districts = TeamDistrictsQuery(team_key="frc254").fetch()
    assert districts == []


def test_get_districts() -> None:
    preseed_district_team(254, "2019ne")
    preseed_district_team(254, "2018ne")

    districts = TeamDistrictsQuery(team_key="frc254").fetch()
    assert len(districts) == 2


def test_get_district_across_rename() -> None:
    preseed_district_team(254, "2019fma")
    preseed_district_team(254, "2018mar")

    districts = TeamDistrictsQuery(team_key="frc254").fetch()
    assert len(districts) == 2
