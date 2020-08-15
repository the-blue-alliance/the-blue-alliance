from typing import List, Optional

from google.cloud import ndb

from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import Year
from backend.common.models.team import Team
from backend.common.queries.team_query import TeamListQuery, TeamListYearQuery


def preseed_teams(start_team: int, end_team: Optional[int] = None) -> List[ndb.Key]:
    end_team = end_team or start_team
    stored = ndb.put_multi(
        [Team(id=f"frc{i}", team_number=i,) for i in range(start_team, end_team + 1)]
    )
    assert len(stored) == (end_team - start_team + 1)
    return stored


def preseed_event_teams(team_keys: List[ndb.Key], event_year: Year) -> None:
    event_teams = [
        EventTeam(
            id=f"{event_year}ct_{t.id()}",
            event=ndb.Key(Event, f"{event_year}ct"),
            team=t,
            year=event_year,
        )
        for t in team_keys
    ]
    ndb.put_multi(event_teams)


def test_no_data() -> None:
    teams = TeamListYearQuery(year=2020, page=1).fetch()
    assert teams == []


def test_no_event_teams() -> None:
    preseed_teams(1, 10)
    teams = TeamListYearQuery(year=2020, page=1).fetch()
    assert teams == []


def test_with_event_teams() -> None:
    stored_teams = preseed_teams(1, 10)
    preseed_event_teams(stored_teams, 2020)

    teams = TeamListYearQuery(year=2020, page=0).fetch()
    assert len(teams) == len(stored_teams)


def test_with_event_teams_wrong_year() -> None:
    stored_teams = preseed_teams(1, 10)
    preseed_event_teams(stored_teams, 2019)

    teams = TeamListYearQuery(year=2020, page=0).fetch()
    assert teams == []


def test_with_event_teams_wrong_page() -> None:
    stored_teams = preseed_teams(1, 10)
    preseed_event_teams(stored_teams, 2020)

    teams = TeamListYearQuery(year=2020, page=10).fetch()
    assert teams == []


def test_affected_queries() -> None:
    stored_teams = preseed_teams(1, 10)
    preseed_event_teams(stored_teams, 2020)

    for team_key in stored_teams:
        assert {
            q.cache_key
            for q in TeamListYearQuery._eventteam_affected_queries(
                event_key="2020test", team_key=team_key.id(), year=2020
            )
        } == {TeamListYearQuery(year=2020, page=0).cache_key}
        assert {
            q.cache_key
            for q in TeamListYearQuery._team_affected_queries(team_key=team_key.id())
        } == {TeamListQuery(page=0).cache_key}
