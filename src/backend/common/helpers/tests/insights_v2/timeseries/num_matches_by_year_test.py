import json

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.timeseries.num_matches_by_year import (
    NumMatchesByYearV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightCategory
from backend.common.models.match import Match

_ALL_TEAMS = ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]


def _alliances_json(red_score: int, blue_score: int) -> str:
    return json.dumps(
        {
            "red": {"score": red_score, "teams": ["frc1", "frc2", "frc3"]},
            "blue": {"score": blue_score, "teams": ["frc4", "frc5", "frc6"]},
        }
    )


def _put_event(
    event_key: str,
    year: int,
    event_type: EventType = EventType.REGIONAL,
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
    ).put()


def _put_match(
    event_key: str,
    year: int,
    match_number: int,
    red_score: int = 10,
    blue_score: int = 5,
) -> None:
    Match(
        id=f"{event_key}_qm{match_number}",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=match_number,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(red_score, blue_score),
    ).put()


def _calc() -> NumMatchesByYearV2Calculator:
    return NumMatchesByYearV2Calculator()


def test_counts_played_matches_per_year(ndb_stub) -> None:
    _put_event("2023nyny", 2023)
    for i in range(1, 4):
        _put_match("2023nyny", 2023, i)

    _put_event("2024nyny", 2024)
    for i in range(1, 6):
        _put_match("2024nyny", 2024, i)

    insights = compute_insights_for_year(0, [_calc()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "num_matches_by_year"
    assert insight.display_name == "Number of Matches by Year"
    assert insight.category == InsightCategory.TIMESERIES
    assert insight.year == 0
    assert insight.key_name == "0_v2_timeseries_num_matches_by_year"

    data = insight.data
    assert data["x_type"] == "year"
    assert len(data["series"]) == 1
    assert data["series"][0]["label"] == "Matches"

    points = data["series"][0]["points"]
    assert points == [
        {"x": 2023, "y": 3.0},
        {"x": 2024, "y": 5.0},
    ]


def test_unplayed_matches_not_counted(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, 1)
    _put_match("2024nyny", 2024, 2, red_score=-1, blue_score=-1)

    insights = compute_insights_for_year(0, [_calc()])

    assert insights[0].data["series"][0]["points"] == [{"x": 2024, "y": 1.0}]


def test_offseason_event_skipped(ndb_stub) -> None:
    _put_event("2024iri", 2024, event_type=EventType.OFFSEASON)
    _put_match("2024iri", 2024, 1)

    insights = compute_insights_for_year(0, [_calc()])

    assert insights == []


def test_no_played_matches_produces_no_insight(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, 1, red_score=-1, blue_score=-1)

    insights = compute_insights_for_year(0, [_calc()])

    assert insights == []
