from __future__ import annotations

from typing import cast

import pytest
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2026
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026
from backend.common.game_specific.seasons.tests.conftest import (
    HELPERS_TESTS,
    tiebreak_winner,
)
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
