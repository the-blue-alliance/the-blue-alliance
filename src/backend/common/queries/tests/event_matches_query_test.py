from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.queries.match_query import (
    EventMatchesQuery,
    EventPracticeMatchesQuery,
)


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


def preseed_practice_matches(n: int) -> None:
    ndb.put_multi(
        [
            Match(
                id=f"2010ct_pm{i}",
                event=ndb.Key(Event, "2010ct"),
                year=2010,
                comp_level=CompLevel.PM,
                set_number=1,
                match_number=i,
                alliances_json="",
            )
            for i in range(1, n + 1)
        ]
    )


def test_excludes_practice_matches() -> None:
    preseed_matches(5)
    preseed_practice_matches(3)
    matches = EventMatchesQuery(event_key="2010ct").fetch()
    assert len(matches) == 5
    assert all(m.comp_level == CompLevel.QM for m in matches)


def test_practice_matches_only() -> None:
    preseed_matches(5)
    preseed_practice_matches(3)
    matches = EventPracticeMatchesQuery(event_key="2010ct").fetch()
    assert len(matches) == 3
    assert all(m.comp_level == CompLevel.PM for m in matches)


def test_no_practice_matches() -> None:
    preseed_matches(5)
    assert EventPracticeMatchesQuery(event_key="2010ct").fetch() == []
