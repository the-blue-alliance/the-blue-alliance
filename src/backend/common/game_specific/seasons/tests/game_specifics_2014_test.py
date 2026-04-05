from __future__ import annotations

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.game_specific.seasons.game_specifics_2014 import GameSpecifics2014


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2014().ranking_sort_order_info() == SORT_ORDER_INFO[2014]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2014().valid_score_breakdown_keys()
    assert "auto" in keys
    assert "assist" in keys
    assert "truss+catch" in keys
    assert "teleop_goal+foul" in keys


def test_tiebreak_criteria_empty() -> None:
    assert GameSpecifics2014().tiebreak_criteria({}, {}) == []


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2014().finals_can_be_tiebroken() is False


def test_record_in_rankings() -> None:
    assert GameSpecifics2014().record_in_rankings() is True


def test_qual_average_in_rankings() -> None:
    assert GameSpecifics2014().qual_average_in_rankings() is False
