import datetime
import json
from typing import Dict, List, Optional

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.game_stats.calculator import (
    GameStatsV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightCategory

_WEEK_1_START = datetime.datetime(2024, 1, 3)
_WEEK_2_START = datetime.datetime(2024, 1, 10)


def _alliances_json(red_score: int, blue_score: int) -> str:
    return json.dumps(
        {
            "red": {
                "score": red_score,
                "teams": ["frc1", "frc2", "frc3"],
                "surrogates": [],
                "dqs": [],
            },
            "blue": {
                "score": blue_score,
                "teams": ["frc4", "frc5", "frc6"],
                "surrogates": [],
                "dqs": [],
            },
        }
    )


def _breakdown_json(
    red_melody: bool,
    blue_melody: bool,
    red_auto: Optional[int],
    blue_auto: Optional[int],
) -> str:
    def alliance(melody: bool, auto: Optional[int]) -> Dict[str, object]:
        breakdown: Dict[str, object] = {
            "melodyBonusAchieved": melody,
            "ensembleBonusAchieved": True,
        }
        if auto is not None:
            breakdown["autoPoints"] = auto
        return breakdown

    return json.dumps(
        {
            "red": alliance(red_melody, red_auto),
            "blue": alliance(blue_melody, blue_auto),
        }
    )


def _put_event(
    event_key: str,
    event_type_enum: int = EventType.REGIONAL,
    start_date: datetime.datetime = _WEEK_1_START,
    official: bool = True,
    short_name: Optional[str] = None,
) -> None:
    Event(
        id=event_key,
        year=2024,
        name=f"{event_key} Regional",
        short_name=short_name,
        event_short=event_key[4:],
        event_type_enum=event_type_enum,
        start_date=start_date,
        official=official,
    ).put()


def _put_match(
    event_key: str,
    match_number: int,
    red_score: int,
    blue_score: int,
    red_melody: bool = True,
    blue_melody: bool = True,
    comp_level: CompLevel = CompLevel.QM,
    with_breakdown: bool = True,
    red_auto: Optional[int] = None,
    blue_auto: Optional[int] = None,
) -> None:
    suffix = str(match_number) if comp_level == CompLevel.QM else f"m{match_number}"
    from backend.common.models.match import Match

    Match(
        id=f"{event_key}_{comp_level}{suffix}",
        comp_level=comp_level,
        event=ndb.Key(Event, event_key),
        year=2024,
        match_number=match_number,
        set_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=_alliances_json(red_score, blue_score),
        score_breakdown_json=(
            _breakdown_json(red_melody, blue_melody, red_auto, blue_auto)
            if with_breakdown
            else None
        ),
    ).put()


def _rates(scope) -> Dict[str, List[int]]:
    return {r["name"]: [r["count"], r["opportunities"]] for r in scope["qual"]}


def _averages(scope, key: str = "qual_averages") -> Dict[str, float]:
    return {a["name"]: a["value"] for a in scope[key]}


def _scopes_of(insight, scope_type: str):
    return [s for s in insight.data["scopes"] if s["scope_type"] == scope_type]


def test_counts_bonus_rps_across_scopes(ndb_stub) -> None:
    _put_event("2024casj", short_name="San Jose")
    _put_match("2024casj", 1, 100, 80, red_melody=True, blue_melody=False)
    _put_match("2024casj", 2, 60, 40, red_melody=True, blue_melody=True)

    insights = compute_insights_for_year(2024, [GameStatsV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "game_stats"
    assert insight.category == InsightCategory.GAME_STATS
    assert insight.year == 2024
    assert insight.district_abbreviation is None

    overall = _scopes_of(insight, "overall")[0]
    assert overall["label"] == "Overall"
    assert overall["key"] is None
    assert overall["week"] is None
    assert _rates(overall) == {
        "rp_1": [3, 4],
        "rp_2": [4, 4],
        "max_alliance_rp": [2, 2],
        "max_match_rp": [1, 2],
    }

    labels = {r["name"]: r["label"] for r in overall["qual"]}
    assert labels == {
        "rp_1": "Melody RP",
        "rp_2": "Ensemble RP",
        "max_alliance_rp": "4 RP",
        "max_match_rp": "6 RP",
    }


def test_averages_across_scopes(ndb_stub) -> None:
    _put_event("2024casj", short_name="San Jose")
    _put_match("2024casj", 1, 100, 80, red_melody=True, blue_melody=False)
    _put_match("2024casj", 2, 60, 40, red_melody=True, blue_melody=True)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    overall = _scopes_of(insight, "overall")[0]
    averages = _averages(overall)
    assert averages["average_score"] == 70.0  # (180 + 100) / (2 * 2)
    assert averages["average_win_margin"] == 20.0  # (20 + 20) / 2
    assert averages["average_winning_score"] == 80.0  # (100 + 60) / 2

    labels = {a["name"]: a["label"] for a in overall["qual_averages"]}
    assert labels["average_score"] == "Average Score"
    assert labels["average_win_margin"] == "Average Win Margin"


def test_week_and_event_scopes(ndb_stub) -> None:
    _put_event("2024casj", start_date=_WEEK_1_START, short_name="San Jose")
    _put_match("2024casj", 1, 100, 80, red_melody=True, blue_melody=False)

    _put_event("2024caln", start_date=_WEEK_2_START, short_name="Central Valley")
    _put_match("2024caln", 1, 60, 40, red_melody=False, blue_melody=False)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    weeks = _scopes_of(insight, "week")
    assert [w["label"] for w in weeks] == ["Week 1", "Week 2"]
    assert [w["week"] for w in weeks] == [0, 1]
    assert _rates(weeks[0])["rp_1"] == [1, 2]
    assert _rates(weeks[1])["rp_1"] == [0, 2]
    assert _averages(weeks[0])["average_score"] == 90.0  # 180 / 2
    assert _averages(weeks[1])["average_score"] == 50.0  # 100 / 2

    events = _scopes_of(insight, "event")
    assert [e["key"] for e in events] == ["2024casj", "2024caln"]
    assert [e["label"] for e in events] == ["San Jose", "Central Valley"]
    assert _rates(events[0])["rp_1"] == [1, 2]
    assert _rates(events[1])["rp_1"] == [0, 2]
    assert _averages(events[0])["average_score"] == 90.0
    assert _averages(events[1])["average_score"] == 50.0


def test_averages_weighted_across_events(ndb_stub) -> None:
    _put_event("2024casj", start_date=_WEEK_1_START, short_name="San Jose")
    _put_match("2024casj", 1, 100, 80)
    _put_match("2024casj", 2, 100, 80)

    _put_event("2024caln", start_date=_WEEK_1_START, short_name="Central Valley")
    _put_match("2024caln", 1, 0, 0)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    overall = _scopes_of(insight, "overall")[0]
    # True combined average: (180 + 180 + 0) / (3 * 2) = 60.0. A naive
    # unweighted mean of the two events' own averages (90.0 and 0.0) would
    # give 45.0 instead - confirming events are weighted by match count.
    assert _averages(overall)["average_score"] == 60.0

    week = _scopes_of(insight, "week")[0]
    assert _averages(week)["average_score"] == 60.0


def test_event_label_falls_back_to_name(ndb_stub) -> None:
    _put_event("2024casj", short_name=None)
    _put_match("2024casj", 1, 100, 80)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    assert _scopes_of(insight, "event")[0]["label"] == "2024casj Regional"


def test_qual_and_playoff_split(ndb_stub) -> None:
    _put_event("2024casj")
    _put_match("2024casj", 1, 100, 80, red_melody=True, blue_melody=True)
    _put_match(
        "2024casj",
        1,
        60,
        40,
        red_melody=False,
        blue_melody=False,
        comp_level=CompLevel.F,
    )

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]
    overall = _scopes_of(insight, "overall")[0]

    qual = {r["name"]: [r["count"], r["opportunities"]] for r in overall["qual"]}
    playoff = {r["name"]: [r["count"], r["opportunities"]] for r in overall["playoff"]}
    assert qual["rp_1"] == [2, 2]
    assert playoff["rp_1"] == [0, 2]

    assert _averages(overall, "qual_averages")["average_score"] == 90.0
    assert _averages(overall, "playoff_averages")["average_score"] == 50.0


def test_championship_scope_sorts_last(ndb_stub) -> None:
    _put_event("2024casj", start_date=_WEEK_1_START)
    _put_match("2024casj", 1, 100, 80)

    _put_event(
        "2024cmptx",
        event_type_enum=EventType.CMP_FINALS,
        start_date=datetime.datetime(2024, 4, 20),
    )
    _put_match("2024cmptx", 1, 200, 160)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    weeks = _scopes_of(insight, "week")
    assert [w["label"] for w in weeks] == ["Week 1", "Championship"]
    assert [w["week"] for w in weeks] == [0, None]


def test_tie_counts_as_a_missed_opportunity(ndb_stub) -> None:
    _put_event("2024casj")
    _put_match("2024casj", 1, 80, 80, red_melody=True, blue_melody=True)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    rates = _rates(_scopes_of(insight, "overall")[0])
    assert rates["max_alliance_rp"] == [0, 1]
    assert rates["max_match_rp"] == [0, 1]


def test_unplayed_matches_skipped(ndb_stub) -> None:
    _put_event("2024casj")
    _put_match("2024casj", 1, -1, -1)

    assert compute_insights_for_year(2024, [GameStatsV2Calculator()]) == []


def test_matches_without_breakdowns_offer_no_opportunities(ndb_stub) -> None:
    _put_event("2024casj")
    _put_match("2024casj", 1, 100, 80, with_breakdown=False)

    assert compute_insights_for_year(2024, [GameStatsV2Calculator()]) == []


def test_offseason_event_skipped(ndb_stub) -> None:
    _put_event(
        "2024iri",
        event_type_enum=EventType.OFFSEASON,
        official=False,
    )
    _put_match("2024iri", 1, 100, 80)

    assert compute_insights_for_year(2024, [GameStatsV2Calculator()]) == []


def test_year_without_bonus_rps_produces_no_insight(ndb_stub) -> None:
    Event(
        id="2014casj",
        year=2014,
        name="San Jose Regional",
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2014, 1, 3),
        official=True,
    ).put()

    assert compute_insights_for_year(2014, [GameStatsV2Calculator()]) == []


def test_key_name(ndb_stub) -> None:
    _put_event("2024casj")
    _put_match("2024casj", 1, 100, 80)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    assert insight.key_name == "2024_v2_game_stats_game_stats"


def test_auto_win_conversion_counted(ndb_stub) -> None:
    _put_event("2024casj")
    _put_match("2024casj", 1, 100, 80, red_auto=20, blue_auto=10)
    _put_match("2024casj", 2, 60, 90, red_auto=20, blue_auto=10)
    _put_match("2024casj", 3, 60, 90, red_auto=10, blue_auto=10)

    insight = compute_insights_for_year(2024, [GameStatsV2Calculator()])[0]

    rates = _rates(_scopes_of(insight, "overall")[0])
    assert rates["auto_win_conversion"] == [1, 2]
