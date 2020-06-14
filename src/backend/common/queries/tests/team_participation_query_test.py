from typing import List

from google.cloud import ndb

from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team
from backend.common.queries.team_query import TeamParticipationQuery


def preseed_event_teams(team: int, event_short: str, years: List[int]) -> None:
    event_teams = [
        EventTeam(
            id=f"{year}{event_short}_frc{team}",
            event=ndb.Key(Event, f"{year}{event_short}"),
            team=ndb.Key(Team, f"frc{team}"),
            year=year,
        )
        for year in years
    ]
    ndb.put_multi(event_teams)


def test_no_data() -> None:
    years = TeamParticipationQuery(team_key="frc254").fetch()
    assert years == set()


def test_other_teams() -> None:
    preseed_event_teams(148, "ct", [2018, 2019, 2020])
    years = TeamParticipationQuery(team_key="frc254").fetch()
    assert years == set()


def test_get_data() -> None:
    preseed_event_teams(254, "ct", [2018, 2019, 2020])

    years = TeamParticipationQuery(team_key="frc254").fetch()
    assert years == {2020, 2019, 2018}
