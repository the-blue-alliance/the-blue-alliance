from google.cloud import ndb
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team
from backend.common.queries.event_query import (
    TeamEventsQuery,
    TeamYearEventsQuery,
    TeamYearEventTeamsQuery,
)
from typing import List, Optional


def preseed_events(year: int, n: int) -> List[str]:
    stored = ndb.put_multi(
        [
            Event(
                id=f"{year}test{i}",
                event_short=f"test{i}",
                year=year,
                event_type_enum=EventType.OFFSEASON,
            )
            for i in range(n)
        ]
    )
    assert len(stored) == n
    return [k.id() for k in stored]


def preseed_teams(start_team: int, end_team: Optional[int] = None) -> None:
    end_team = end_team or start_team
    stored = ndb.put_multi(
        [Team(id=f"frc{i}", team_number=i,) for i in range(start_team, end_team + 1)]
    )
    assert len(stored) == (end_team - start_team + 1)


def preseed_event_team(team_key: str, event_keys: List[str]) -> None:
    [
        EventTeam(
            id=f"{event_key}_{team_key}",
            event=ndb.Key(Event, event_key),
            team=ndb.Key(Team, team_key),
            year=int(event_key[:4]),
        ).put()
        for event_key in event_keys
    ]


def test_team_events_no_data() -> None:
    events = TeamEventsQuery(team_key="frc254").fetch()
    assert events == []


def test_team_year_events_no_data() -> None:
    events = TeamYearEventsQuery(team_key="frc254", year=2020).fetch()
    assert events == []


def test_team_year_event_teams_no_data() -> None:
    event_teams = TeamYearEventTeamsQuery(team_key="frc254", year=2020).fetch()
    assert event_teams == []


def test_team_events() -> None:
    events1 = preseed_events(2020, 1)
    events2 = preseed_events(2019, 1)
    preseed_teams(254)
    preseed_event_team("frc254", events1 + events2)

    event_teams = TeamEventsQuery(team_key="frc254").fetch()
    assert len(event_teams) == 2


def test_team_year_events() -> None:
    events1 = preseed_events(2020, 1)
    events2 = preseed_events(2019, 1)
    preseed_teams(254)
    preseed_event_team("frc254", events1 + events2)

    event_teams = TeamYearEventTeamsQuery(team_key="frc254", year=2020).fetch()
    assert len(event_teams) == 1


def test_team_year_event_teams() -> None:
    events1 = preseed_events(2020, 1)
    events2 = preseed_events(2019, 1)
    preseed_teams(254)
    preseed_event_team("frc254", events1 + events2)

    event_teams = TeamYearEventTeamsQuery(team_key="frc254", year=2020).fetch()
    assert len(event_teams) == 1
