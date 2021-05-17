from google.cloud import ndb

from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey
from backend.common.models.team import Team
from backend.common.queries.team_query import EventEventTeamsQuery


def preseed_event_teams(start_team: int, end_team: int, event_key: EventKey) -> None:
    event_teams = [
        EventTeam(
            id=f"{event_key}_frc{t}",
            event=ndb.Key(Event, event_key),
            team=ndb.Key(Team, f"frc{t}"),
            year=int(event_key[:4]),
        )
        for t in range(start_team, end_team + 1)
    ]
    ndb.put_multi(event_teams)


def test_no_data() -> None:
    event_teams = EventEventTeamsQuery(event_key="2020ct").fetch()
    assert event_teams == []


def test_get_data() -> None:
    preseed_event_teams(1, 10, "2020ct")

    event_teams = EventEventTeamsQuery(event_key="2020ct").fetch()
    assert len(event_teams) == 10
