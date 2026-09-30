from __future__ import annotations

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2025
from backend.common.game_specific.seasons.game_specifics_2025 import GameSpecifics2025
from backend.common.game_specific.seasons.tests.conftest import (
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
    assert GameSpecifics2025().ranking_sort_order_info() == SORT_ORDER_INFO[2025]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2025().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2025().finals_can_be_tiebroken() is False


def test_tiebreak_criteria_fouls(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2025nhsal_sf7m1.json")
    match: Match = none_throws(Match.get_by_id("2025nhsal_sf7m1"))
    red = cast(
        ScoreDetailModelAlliance2025,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2025,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2025().tiebreak_criteria(red, blue))
        == AllianceColor.BLUE
    )


def test_tiebreak_criteria_auto(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2025vagle_sf8m1.json")
    match: Match = none_throws(Match.get_by_id("2025vagle_sf8m1"))
    red = cast(
        ScoreDetailModelAlliance2025,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2025,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2025().tiebreak_criteria(red, blue))
        == AllianceColor.BLUE
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2025mndu_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2025mndu")).fetch()
    insights = GameSpecifics2025().calculate_event_insights(matches)
    assert insights is not None


def test_get_manual_coprs() -> None:
    coprs = GameSpecifics2025().get_manual_coprs()
    assert len(coprs) > 0


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2025().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_prediction_ranking_fields() -> None:
    game = GameSpecifics2025()
    assert game.ranking_bonus_rp_breakdown_fields() == [
        "autoBonusAchieved",
        "coralBonusAchieved",
        "bargeBonusAchieved",
    ]
    assert game.ranking_bonus_rp_prediction_fields() == [
        "prob_auto_coral_bonus",
        "prob_coral_bonus",
        "prob_barge_bonus",
    ]
    assert game.ranking_tiebreaker_breakdown_field() == "totalPoints"
    assert game.ranking_tiebreaker_prediction_field() == "score"
    assert game.ranking_win_points() == 3


def test_tiebreak_criteria_without_breakdown_data() -> None:
    empty = cast(ScoreDetailModelAlliance2025, {})
    criteria = GameSpecifics2025().tiebreak_criteria(empty, empty)
    assert criteria == [None] * 3
    assert tiebreak_winner(criteria) == ""


def _insights(matches: list[Match]) -> EventInsights:
    return none_throws(GameSpecifics2025().calculate_event_insights(matches))


def test_calculate_event_insights_without_finished_matches() -> None:
    unplayed = build_match("2025test", "qm", 1, -1, -1, None)
    assert _insights([]) == {"qual": None, "playoff": None}
    assert _insights([unplayed]) == {"qual": None, "playoff": None}


def test_calculate_event_insights_scores_matches_without_breakdowns() -> None:
    # Documents current behaviour: a played match with no breakdown counts
    # towards every denominator and the high score, but its scores are never
    # added to the totals, so the averages read 0.0.
    match = build_match("2025test", "qm", 1, 30, 10, None)
    insights = _insights([match])
    assert insights["playoff"] is None
    assert insights["qual"] == {
        "auto_rp_count": [0, 2, 0.0],
        "barge_rp_count": [0, 2, 0.0],
        "coral_rp_count": [0, 2, 0.0],
        "coopertition_count": [0, 2, 0.0],
        "six_rp_count": [0, 1, 0.0],
        "nine_rp_count": [0, 1, 0.0],
        "average_score": 0.0,
        "average_win_margin": 0.0,
        "average_winning_score": 0.0,
        "high_score": (30, "2025test_qm1", "Q1"),
    }


def test_calculate_event_insights_counts_coopertition_and_rp_sweeps() -> None:
    swept = {
        "autoBonusAchieved": True,
        "bargeBonusAchieved": True,
        "coralBonusAchieved": True,
        "coopertitionCriteriaMet": True,
    }
    both_sweep = build_match("2025test", "qm", 1, 30, 10, {"red": swept, "blue": swept})
    qual = none_throws(_insights([both_sweep])["qual"])
    assert qual["auto_rp_count"] == [2, 2, 100.0]
    assert qual["barge_rp_count"] == [2, 2, 100.0]
    assert qual["coral_rp_count"] == [2, 2, 100.0]
    assert qual["coopertition_count"] == [2, 2, 100.0]
    assert qual["six_rp_count"] == [1, 1, 100.0]
    assert qual["nine_rp_count"] == [1, 1, 100.0]

    # Only the winner counts towards the 6 RP sweep, and 9 RP needs both.
    loser_sweeps = build_match("2025test", "qm", 2, 30, 10, {"red": {}, "blue": swept})
    qual = none_throws(_insights([loser_sweeps])["qual"])
    assert qual["six_rp_count"] == [0, 1, 0.0]
    assert qual["nine_rp_count"] == [0, 1, 0.0]

    winner_sweeps = build_match("2025test", "qm", 3, 30, 10, {"red": swept, "blue": {}})
    qual = none_throws(_insights([winner_sweeps])["qual"])
    assert qual["six_rp_count"] == [1, 1, 100.0]
    assert qual["nine_rp_count"] == [0, 1, 0.0]

    # A tie has no winner, so neither sweep is awarded.
    tie = build_match("2025test", "qm", 4, 20, 20, {"red": swept, "blue": swept})
    qual = none_throws(_insights([tie])["qual"])
    assert qual["six_rp_count"] == [0, 1, 0.0]
    assert qual["nine_rp_count"] == [0, 1, 0.0]
