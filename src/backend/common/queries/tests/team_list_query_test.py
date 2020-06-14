from typing import Optional

from google.cloud import ndb

from backend.common.models.team import Team
from backend.common.queries.team_query import TeamListQuery


def preseed_teams(start_team: int, end_team: Optional[int] = None) -> None:
    end_team = end_team or start_team
    stored = ndb.put_multi(
        [Team(id=f"frc{i}", team_number=i,) for i in range(start_team, end_team + 1)]
    )
    assert len(stored) == (end_team - start_team + 1)


def test_no_teams() -> None:
    teams = TeamListQuery(page=0).fetch()
    assert teams == []


def test_single_team() -> None:
    preseed_teams(1)
    teams = TeamListQuery(page=0).fetch()
    assert len(teams) == 1
    assert teams[0].team_number == 1


def test_multiple_teams() -> None:
    preseed_teams(1, 5)
    teams = TeamListQuery(page=0).fetch()
    assert len(teams) == 5
    for team_number, team in zip(range(1, 6), teams):
        assert team.team_number == team_number


def test_teams_are_ordered() -> None:
    preseed_teams(4)
    preseed_teams(2)
    preseed_teams(10)
    teams = TeamListQuery(page=0).fetch()
    assert len(teams) == 3
    for team_number, team in zip([2, 4, 10], teams):
        assert team.team_number == team_number


def test_lower_bound_inclusive() -> None:
    preseed_teams(500)
    teams = TeamListQuery(page=1).fetch()
    assert len(teams) == 1
    assert teams[0].team_number == 500


def test_upper_bound_exclusive() -> None:
    preseed_teams(500)
    teams = TeamListQuery(page=0).fetch()
    assert teams == []
