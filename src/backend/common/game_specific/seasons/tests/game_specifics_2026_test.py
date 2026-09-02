from __future__ import annotations

import json
from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2026
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026
from backend.common.game_specific.seasons.tests.conftest import (
    HELPERS_TESTS,
    tiebreak_winner,
)
from backend.common.models.event import Event
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


def _success_rate_match(
    red_score: int,
    blue_score: int,
    red: dict | None = None,
    blue: dict | None = None,
) -> Match:
    def alliance(overrides: dict | None) -> dict:
        breakdown = {
            "energizedAchieved": False,
            "superchargedAchieved": False,
            "traversalAchieved": False,
            "totalAutoPoints": 0,
            "hubScore": {
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
        breakdown.update(overrides or {})
        return breakdown

    return Match(
        id="2026casj_qm1",
        comp_level="qm",
        event=ndb.Key(Event, "2026casj"),
        year=2026,
        match_number=1,
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
    match = _success_rate_match(
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
    rates = _measure(_success_rate_match(100, 80, red=swept))
    assert rates["max_alliance_rp"] == (1, 1)
    assert rates["max_match_rp"] == (0, 1)

    rates = _measure(_success_rate_match(100, 80, red=swept, blue=swept))
    assert rates["max_alliance_rp"] == (1, 1)
    assert rates["max_match_rp"] == (1, 1)

    rates = _measure(_success_rate_match(80, 100, red=swept))
    assert rates["max_alliance_rp"] == (0, 1)


def test_success_rate_tie_is_a_missed_rp_opportunity() -> None:
    swept = {
        "energizedAchieved": True,
        "superchargedAchieved": True,
        "traversalAchieved": True,
    }
    rates = _measure(_success_rate_match(80, 80, red=swept, blue=swept))
    assert rates["max_alliance_rp"] == (0, 1)
    assert rates["max_match_rp"] == (0, 1)


def test_success_rate_climbs_counted_per_robot() -> None:
    match = _success_rate_match(
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
    match = _success_rate_match(100, 80, red={"totalAutoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (1, 1)

    match = _success_rate_match(80, 100, red={"totalAutoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (0, 1)


def test_success_rate_auto_win_conversion_needs_both_winners() -> None:
    match = _success_rate_match(100, 80)
    assert _measure(match)["auto_win_conversion"] == (0, 0)

    match = _success_rate_match(80, 80, red={"totalAutoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (0, 0)


def test_success_rate_counters_skip_matches_without_breakdowns() -> None:
    match = _success_rate_match(100, 80)
    match.score_breakdown_json = None
    match._score_breakdown = None
    assert set(_measure(match).values()) == {(0, 0)}
