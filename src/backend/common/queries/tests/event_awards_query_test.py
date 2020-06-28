from google.cloud import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.queries.award_query import EventAwardsQuery


def test_no_awards() -> None:
    awards = EventAwardsQuery(event_key="2010ct").fetch()
    assert awards == []


def test_query() -> None:
    a = Award(
        id="2010ct_1",
        year=2010,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2010ct"),
        name_str="Winner",
    )
    a.put()

    awards = EventAwardsQuery(event_key="2010ct").fetch()
    assert awards == [a]
