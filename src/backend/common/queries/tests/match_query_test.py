from google.cloud import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.queries.match_query import MatchQuery


def test_no_match() -> None:
    match = MatchQuery(match_key="2010ct_qm1").fetch()
    assert match is None


def test_match_exists() -> None:
    Match(
        id="2010ct_qm1",
        event=ndb.Key(Event, "2010ct"),
        year=2010,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json="",
    ).put()

    match = MatchQuery(match_key="2010ct_qm1").fetch()
    assert match == Match.get_by_id("2010ct_qm1")
