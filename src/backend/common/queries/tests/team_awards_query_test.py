from google.cloud import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.award_query import TeamAwardsQuery


def test_no_awards() -> None:
    awards = TeamAwardsQuery(team_key="frc254").fetch()
    assert awards == []


def test_query() -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    )
    a.put()

    awards = TeamAwardsQuery(team_key="frc254").fetch()
    assert awards == [a]
