from google.cloud import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.award_query import TeamEventAwardsQuery


def test_no_awards() -> None:
    awards = TeamEventAwardsQuery(team_key="frc254", event_key="2010ct").fetch()
    assert awards == []


def test_query() -> None:
    a1 = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    )
    a1.put()

    a2 = Award(
        id="2011ct_1",
        year=2011,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2011ct"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    )
    a2.put()

    awards = TeamEventAwardsQuery(team_key="frc254", event_key="2010ct").fetch()
    assert awards == [a1]
