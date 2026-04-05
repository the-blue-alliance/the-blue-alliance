from __future__ import annotations

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.game_specific.seasons.game_specifics_2021 import GameSpecifics2021


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2021().ranking_sort_order_info() == SORT_ORDER_INFO[2021]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2021().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_record_in_rankings() -> None:
    assert GameSpecifics2021().record_in_rankings() is False


def test_round_robin_tiebreak_keys() -> None:
    assert GameSpecifics2021().round_robin_tiebreak_keys() == []


def test_round_robin_tiebreaker_names() -> None:
    assert GameSpecifics2021().round_robin_tiebreaker_names() == []
