from __future__ import annotations

import json
from typing import Any, cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2026
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026
from backend.common.game_specific.seasons.tests.conftest import (
    assert_breakdownless_match_excluded,
    build_match,
    HELPERS_TESTS,
    tiebreak_winner,
)
from backend.common.models.event import Event
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2026().ranking_sort_order_info() == SORT_ORDER_INFO[2026]


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2026().finals_can_be_tiebroken() is False


def test_tiebreak_criteria_auto_fuel(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2026paphi_sf10m1.json")
    match: Match = none_throws(Match.get_by_id("2026paphi_sf10m1"))
    red = cast(
        ScoreDetailModelAlliance2026,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2026,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2026().tiebreak_criteria(red, blue))
        == AllianceColor.BLUE
    )


def test_tiebreak_criteria_major_foul(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2026schop_sf5m1.json")
    match: Match = none_throws(Match.get_by_id("2026schop_sf5m1"))
    red = cast(
        ScoreDetailModelAlliance2026,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2026,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2026().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_get_manual_coprs() -> None:
    coprs = GameSpecifics2026().get_manual_coprs()
    assert len(coprs) > 0


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2026().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_prediction_ranking_fields() -> None:
    game = GameSpecifics2026()
    assert game.ranking_bonus_rp_breakdown_fields() == [
        "energizedAchieved",
        "superchargedAchieved",
        "traversalAchieved",
    ]
    assert game.ranking_bonus_rp_prediction_fields() == [
        "prob_energized_bonus",
        "prob_supercharged_bonus",
        "prob_traversal_bonus",
    ]
    assert game.ranking_tiebreaker_breakdown_field() == "totalPoints"
    assert game.ranking_tiebreaker_prediction_field() == "score"
    assert game.ranking_win_points() == 3


def _build_match(
    red_score: int,
    blue_score: int,
    red: dict | None = None,
    blue: dict | None = None,
    match_number: int = 1,
) -> Match:
    def alliance(overrides: dict | None) -> dict:
        breakdown: dict[str, Any] = {
            "energizedAchieved": False,
            "superchargedAchieved": False,
            "traversalAchieved": False,
            "totalAutoPoints": 0,
            "hubScore": {
                "autoCount": 0,
                "teleopCount": 0,
                "shift1Count": 0,
                "shift2Count": 0,
                "shift3Count": 0,
                "shift4Count": 0,
            },
            "autoTowerRobot1": "None",
            "autoTowerRobot2": "None",
            "autoTowerRobot3": "None",
            "endGameTowerRobot1": "None",
            "endGameTowerRobot2": "None",
            "endGameTowerRobot3": "None",
        }
        overrides = dict(overrides or {})
        breakdown["hubScore"].update(overrides.pop("hubScore", {}))
        breakdown.update(overrides)
        return breakdown

    return Match(
        id=f"2026casj_qm{match_number}",
        comp_level="qm",
        event=ndb.Key(Event, "2026casj"),
        year=2026,
        match_number=match_number,
        set_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=json.dumps(
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
        ),
        score_breakdown_json=json.dumps({"red": alliance(red), "blue": alliance(blue)}),
    )


def _measure(match: Match) -> dict:
    return {
        counter.name: counter.measure(match)
        for counter in GameSpecifics2026().success_rate_counters()
    }


def test_success_rate_counter_names_and_labels() -> None:
    counters = GameSpecifics2026().success_rate_counters()
    assert [(c.name, c.label) for c in counters] == [
        ("rp_1", "Energized RP"),
        ("rp_2", "Supercharged RP"),
        ("rp_3", "Traversal RP"),
        ("max_alliance_rp", "6 RP"),
        ("max_match_rp", "9 RP"),
        ("auto_win_conversion", "Auto Win Conversion"),
        ("auto_climb", "Auto Climb"),
        ("level1_climb", "Level 1 Climb"),
        ("level2_climb", "Level 2 Climb"),
        ("level3_climb", "Level 3 Climb"),
    ]


def test_success_rate_bonus_rps_counted_per_alliance() -> None:
    match = _build_match(
        100,
        80,
        red={"energizedAchieved": True, "superchargedAchieved": True},
        blue={"energizedAchieved": True},
    )
    rates = _measure(match)
    assert rates["rp_1"] == (2, 2)
    assert rates["rp_2"] == (1, 2)
    assert rates["rp_3"] == (0, 2)


def test_success_rate_winner_sweep_awards_six_rp() -> None:
    swept = {
        "energizedAchieved": True,
        "superchargedAchieved": True,
        "traversalAchieved": True,
    }
    rates = _measure(_build_match(100, 80, red=swept))
    assert rates["max_alliance_rp"] == (1, 1)
    assert rates["max_match_rp"] == (0, 1)

    rates = _measure(_build_match(100, 80, red=swept, blue=swept))
    assert rates["max_alliance_rp"] == (1, 1)
    assert rates["max_match_rp"] == (1, 1)

    rates = _measure(_build_match(80, 100, red=swept))
    assert rates["max_alliance_rp"] == (0, 1)


def test_success_rate_tie_is_a_missed_rp_opportunity() -> None:
    swept = {
        "energizedAchieved": True,
        "superchargedAchieved": True,
        "traversalAchieved": True,
    }
    rates = _measure(_build_match(80, 80, red=swept, blue=swept))
    assert rates["max_alliance_rp"] == (0, 1)
    assert rates["max_match_rp"] == (0, 1)


def test_success_rate_climbs_counted_per_robot() -> None:
    match = _build_match(
        100,
        80,
        red={
            "autoTowerRobot1": "Level1",
            "autoTowerRobot2": "Level3",
            "endGameTowerRobot1": "Level1",
            "endGameTowerRobot2": "Level2",
            "endGameTowerRobot3": "Level3",
        },
        blue={"autoTowerRobot1": "Level2", "endGameTowerRobot1": "Level1"},
    )
    rates = _measure(match)
    assert rates["auto_climb"] == (3, 6)
    assert rates["level1_climb"] == (2, 6)
    assert rates["level2_climb"] == (1, 6)
    assert rates["level3_climb"] == (1, 6)


def test_success_rate_auto_win_conversion() -> None:
    match = _build_match(100, 80, red={"totalAutoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (1, 1)

    match = _build_match(80, 100, red={"totalAutoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (0, 1)


def test_success_rate_auto_win_conversion_needs_both_winners() -> None:
    match = _build_match(100, 80)
    assert _measure(match)["auto_win_conversion"] == (0, 0)

    match = _build_match(80, 80, red={"totalAutoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (0, 0)


def test_success_rate_counters_skip_matches_without_breakdowns() -> None:
    match = _build_match(100, 80)
    match.score_breakdown_json = None
    match._score_breakdown = None
    assert set(_measure(match).values()) == {(0, 0)}


def test_tiebreak_criteria_without_breakdown_data() -> None:
    empty = cast(ScoreDetailModelAlliance2026, {})
    criteria = GameSpecifics2026().tiebreak_criteria(empty, empty)
    assert criteria == [None, None, None]
    assert tiebreak_winner(criteria) == ""

    # A hubScore that does not record autoPoints cannot break the tie either.
    no_auto = cast(ScoreDetailModelAlliance2026, {"hubScore": {}})
    assert GameSpecifics2026().tiebreak_criteria(no_auto, no_auto)[1] is None


def _auto(fuel: int, **shifts: int) -> dict[str, Any]:
    """
    An alliance breakdown whose AUTO points are all AUTO FUEL, so
    totalAutoPoints and hubScore.autoPoints agree. Which of the two decides the
    AUTO winner is covered separately.
    """
    hub: dict[str, int] = {
        f"shift{i}Count": shifts.get(f"shift{i}", 0) for i in range(1, 5)
    }
    hub["autoPoints"] = fuel
    hub["autoCount"] = fuel
    return {"totalAutoPoints": fuel, "autoTowerPoints": 0, "hubScore": hub}


@pytest.mark.parametrize(
    "red, blue, expected",
    [
        # More AUTO FUEL wins outright.
        (
            _auto(10),
            _auto(5),
            AllianceColor.RED,
        ),
        (
            _auto(5),
            _auto(10),
            AllianceColor.BLUE,
        ),
        # AUTO tied: the AUTO winner's HUB is inactive in SHIFT 1, so whichever
        # alliance scored during SHIFT 1 must have lost AUTO (2026 Game Manual,
        # Version TU22, Section 6.4.1, Table 6-3).
        (
            _auto(5, shift1=3),
            _auto(5),
            AllianceColor.BLUE,
        ),
        (
            _auto(5),
            _auto(5, shift1=3),
            AllianceColor.RED,
        ),
        # Nothing scored in SHIFT 1: the AUTO winner's HUB is active in SHIFT 2.
        (
            _auto(5, shift2=3),
            _auto(5),
            AllianceColor.RED,
        ),
        (
            _auto(5),
            _auto(5, shift2=3),
            AllianceColor.BLUE,
        ),
        # SHIFT 3 mirrors SHIFT 1, SHIFT 4 mirrors SHIFT 2.
        (
            _auto(5, shift3=3),
            _auto(5),
            AllianceColor.BLUE,
        ),
        (
            _auto(5),
            _auto(5, shift3=3),
            AllianceColor.RED,
        ),
        (
            _auto(5, shift4=3),
            _auto(5),
            AllianceColor.RED,
        ),
        (
            _auto(5),
            _auto(5, shift4=3),
            AllianceColor.BLUE,
        ),
        # Nobody scored in any shift: no way to tell who won AUTO.
        (_auto(5), _auto(5), None),
    ],
)
def test_determine_auto_winner(
    red: dict[str, Any], blue: dict[str, Any], expected: AllianceColor | None
) -> None:
    assert GameSpecifics2026().determine_auto_winner(red, blue) == expected


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2026marea_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2026marea")).fetch()
    insights = GameSpecifics2026().calculate_event_insights(matches)
    with open(
        test_data_importer._get_path(HELPERS_TESTS, "data/2026marea_insights.json"),
        "r",
    ) as f:
        expected = json.load(f)
    for level in ("qual", "playoff"):
        expected[level]["high_score"] = tuple(expected[level]["high_score"])
    assert insights == expected


def _insights(matches: list[Match]) -> EventInsights:
    return none_throws(GameSpecifics2026().calculate_event_insights(matches))


def test_calculate_event_insights_without_finished_matches() -> None:
    unplayed = build_match("2026casj", "qm", 1, -1, -1, None)
    assert _insights([]) == {"qual": None, "playoff": None}
    assert _insights([unplayed]) == {"qual": None, "playoff": None}


def test_calculate_event_insights_counts_bonus_rps_and_sweeps() -> None:
    swept = {
        "energizedAchieved": True,
        "superchargedAchieved": True,
        "traversalAchieved": True,
    }
    matches = [
        # Red wins and both alliances sweep: 6 RP for red, 9 RP in the match.
        _build_match(30, 10, red=swept, blue=swept, match_number=1),
        # Blue wins with a sweep, red earns nothing: 6 RP only.
        _build_match(10, 30, blue=swept, match_number=2),
        # Blue sweeps but loses: neither.
        _build_match(30, 10, blue=swept, match_number=3),
        # A tie has no winner, so neither sweep is awarded.
        _build_match(20, 20, red=swept, blue=swept, match_number=4),
    ]
    qual = none_throws(_insights(matches)["qual"])
    assert qual["energized_rp_count"] == [6, 8, 75.0]
    assert qual["supercharged_rp_count"] == [6, 8, 75.0]
    assert qual["traversal_rp_count"] == [6, 8, 75.0]
    assert qual["six_rp_count"] == [2, 4, 50.0]
    assert qual["nine_rp_count"] == [1, 4, 25.0]
    assert qual["average_score"] == 20.0
    assert qual["average_win_margin"] == 15.0
    assert qual["average_winning_score"] == 27.5
    assert qual["high_score"] == (30, "2026casj_qm1", "Q1")


def test_calculate_event_insights_auto_win_conversion() -> None:
    matches = [
        # AUTO winner goes on to win the match.
        _build_match(30, 10, red={"totalAutoPoints": 10}, match_number=1),
        _build_match(10, 30, blue={"totalAutoPoints": 10}, match_number=2),
        # AUTO winner loses the match.
        _build_match(30, 10, blue={"totalAutoPoints": 10}, match_number=3),
        # Undefined: AUTO tied with no shift scoring, or the match tied.
        _build_match(30, 10, match_number=4),
        _build_match(20, 20, red={"totalAutoPoints": 10}, match_number=5),
    ]
    qual = none_throws(_insights(matches)["qual"])
    assert qual["auto_win_conversion"] == [2, 3, 100.0 * 2 / 3]


def test_calculate_event_insights_auto_win_conversion_never_defined() -> None:
    qual = none_throws(_insights([_build_match(30, 10)])["qual"])
    assert qual["auto_win_conversion"] == [0, 0, 0]


def test_calculate_event_insights_counts_fuel_and_climbs() -> None:
    match = _build_match(
        30,
        10,
        red={
            "hubScore": {"autoCount": 12, "teleopCount": 40},
            "autoTowerRobot1": "Level1",
            "endGameTowerRobot1": "Level1",
            "endGameTowerRobot2": "Level2",
            "endGameTowerRobot3": "Level3",
        },
        blue={
            "hubScore": {"autoCount": 8, "teleopCount": 20},
            "autoTowerRobot2": "Level1",
            "endGameTowerRobot1": "Level1",
            "endGameTowerRobot2": "Level2",
            "endGameTowerRobot3": "Level3",
        },
    )
    qual = none_throws(_insights([match])["qual"])
    assert qual["auto_fuel_scored"] == [20, 10.0, 20 / 6]
    assert qual["teleop_fuel_scored"] == [60, 30.0, 10.0]
    assert qual["total_fuel_scored"] == [80, 40.0, 80 / 6]
    # Only two robots per alliance may reach LEVEL 1 during AUTO.
    assert qual["auto_climb_count"] == [2, 4, 50.0]
    assert qual["level1_climb_count"] == [2, 6, 100.0 * 2 / 6]
    assert qual["level2_climb_count"] == [2, 6, 100.0 * 2 / 6]
    assert qual["level3_climb_count"] == [2, 6, 100.0 * 2 / 6]


def test_calculate_event_insights_splits_quals_and_playoffs() -> None:
    breakdown = json.loads(none_throws(_build_match(30, 10).score_breakdown_json))
    playoff = build_match("2026casj", "f", 1, 30, 10, breakdown)
    insights = _insights([playoff])
    assert insights["qual"] is None
    assert none_throws(insights["playoff"])["high_score"] == (30, "2026casj_f1m1", "F1")


def test_breakdownless_match_excluded_from_insights(
    test_data_importer,
) -> None:
    """A played match without a score breakdown leaves every insight unchanged."""
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2026marea_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2026marea")).fetch()
    assert_breakdownless_match_excluded(GameSpecifics2026(), matches)
