from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.award_query import (
    EventTypeAwardsQuery,
    YearEventTypeAwardsQuery,
)


def _award(year: int, event_type: EventType, award_type: AwardType) -> Award:
    event_key = f"{year}{event_type.name.lower()}"
    award = Award(
        id=f"{event_key}_{award_type.value}",
        year=year,
        award_type_enum=award_type,
        event_type_enum=event_type,
        event=ndb.Key(Event, event_key),
        name_str="Award",
        team_list=[ndb.Key(Team, "frc254")],
    )
    award.put()
    return award


def test_event_type_awards_query() -> None:
    a = _award(2010, EventType.REGIONAL, AwardType.WINNER)
    b = _award(2011, EventType.REGIONAL, AwardType.WINNER)
    _award(2010, EventType.DISTRICT, AwardType.WINNER)
    _award(2010, EventType.REGIONAL, AwardType.FINALIST)

    awards = EventTypeAwardsQuery(
        event_type=EventType.REGIONAL, award_type=AwardType.WINNER
    ).fetch()
    assert sorted(awards, key=lambda x: x.year) == [a, b]


def test_year_event_type_awards_query() -> None:
    a = _award(2010, EventType.REGIONAL, AwardType.WINNER)
    _award(2011, EventType.REGIONAL, AwardType.WINNER)
    _award(2010, EventType.DISTRICT, AwardType.WINNER)

    awards = YearEventTypeAwardsQuery(
        year=2010, event_type=EventType.REGIONAL, award_type=AwardType.WINNER
    ).fetch()
    assert awards == [a]
