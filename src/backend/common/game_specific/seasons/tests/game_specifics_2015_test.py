from __future__ import annotations

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.game_specific.seasons.game_specifics_2015 import GameSpecifics2015


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2015().ranking_sort_order_info() == SORT_ORDER_INFO[2015]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2015().valid_score_breakdown_keys()
    assert "coopertition_points" in keys
    assert "auto_points" in keys
    assert "container_points" in keys
    assert "tote_points" in keys
    assert "litter_points" in keys
    assert "foul_points" in keys


def test_tiebreak_criteria_empty() -> None:
    assert GameSpecifics2015().tiebreak_criteria({}, {}) == []


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2015().finals_can_be_tiebroken() is False


def test_record_in_rankings() -> None:
    assert GameSpecifics2015().record_in_rankings() is False


def test_qual_average_in_rankings() -> None:
    assert GameSpecifics2015().qual_average_in_rankings() is True
