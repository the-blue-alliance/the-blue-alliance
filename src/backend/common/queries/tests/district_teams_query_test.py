from typing import List, Optional

from google.cloud import ndb

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.keys import DistrictKey
from backend.common.models.team import Team
from backend.common.queries.team_query import DistrictTeamsQuery


def preseed_teams(start_team: int, end_team: Optional[int] = None) -> List[ndb.Key]:
    end_team = end_team or start_team
    stored = ndb.put_multi(
        [Team(id=f"frc{i}", team_number=i,) for i in range(start_team, end_team + 1)]
    )
    assert len(stored) == (end_team - start_team + 1)
    return stored


def preseed_district_teams(team_keys: List[ndb.Key], district_key: DistrictKey) -> None:
    district_teams = [
        DistrictTeam(
            id=f"{district_key}_{t.id()}",
            team=t,
            district_key=ndb.Key(District, district_key),
            year=int(district_key[:4]),
        )
        for t in team_keys
    ]
    ndb.put_multi(district_teams)


def test_no_teams() -> None:
    teams = DistrictTeamsQuery(district_key="2019ne").fetch()
    assert teams == []


def test_get_teams() -> None:
    stored_teams = preseed_teams(1, 10)
    preseed_district_teams(stored_teams, "2019ne")

    teams = DistrictTeamsQuery(district_key="2019ne").fetch()
    assert len(teams) == len(stored_teams)
