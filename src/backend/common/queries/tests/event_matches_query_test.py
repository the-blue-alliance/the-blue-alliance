from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.queries.match_query import EventMatchesQuery


def preseed_matches(n: int) -> None:
    matches = [
        Match(
            id=f"2010ct_qm{i}",
            event=ndb.Key(Event, "2010ct"),
            year=2010,
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=i,
            alliances_json="",
        )
        for i in range(1, n + 1)
    ]
    ndb.put_multi(matches)


def test_no_matches() -> None:
    matches = EventMatchesQuery(event_key="2010ct").fetch()
    assert matches == []


def test_matches_exist() -> None:
    preseed_matches(5)
    matches = EventMatchesQuery(event_key="2010ct").fetch()
    assert len(matches) == 5
