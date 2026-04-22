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
    HELPERS_TESTS,
    tiebreak_winner,
)
from backend.common.models.event import Event
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
