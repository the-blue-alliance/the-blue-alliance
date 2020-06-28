from typing import List

from google.cloud import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.match import Match
from backend.common.queries.match_query import TeamYearMatchesQuery


def preseed_matches(n: int, event_key: EventKey, team_keys: List[TeamKey]) -> None:
    matches = [
        Match(
            id=f"{event_key}_qm{i}",
            event=ndb.Key(Event, event_key),
            year=int(event_key[:4]),
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=i,
            alliances_json="",
            team_key_names=team_keys,
        )
        for i in range(1, n + 1)
    ]
    ndb.put_multi(matches)


def test_no_matches() -> None:
    matches = TeamYearMatchesQuery(team_key="frc254", year=2010).fetch()
    assert matches == []


def test_matches_exist() -> None:
    preseed_matches(5, "2010ct", ["frc254"])
    preseed_matches(5, "2010nyc", ["frc254"])
    matches = TeamYearMatchesQuery(team_key="frc254", year=2010).fetch()
    assert len(matches) == 10


def test_matches_exist_across_years() -> None:
    preseed_matches(5, "2010ct", ["frc254"])
    preseed_matches(5, "2011ct", ["frc254"])
    matches = TeamYearMatchesQuery(team_key="frc254", year=2010).fetch()
    assert len(matches) == 5
