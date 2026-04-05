from __future__ import annotations

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.game_specific.seasons.game_specifics_2009 import GameSpecifics2009


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2009().ranking_sort_order_info() == SORT_ORDER_INFO[2009]


def test_tiebreak_criteria_empty() -> None:
    assert GameSpecifics2009().tiebreak_criteria({}, {}) == []


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2009().finals_can_be_tiebroken() is False


def test_record_in_rankings() -> None:
    assert GameSpecifics2009().record_in_rankings() is True


def test_qual_average_in_rankings() -> None:
    assert GameSpecifics2009().qual_average_in_rankings() is False
