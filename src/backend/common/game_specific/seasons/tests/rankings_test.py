import pytest

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.game_specific.registry import _REGISTRY, get_game

NO_RECORD_YEARS = [y for y, g in _REGISTRY.items() if not g.record_in_rankings()]
RECORD_YEARS = [y for y, g in _REGISTRY.items() if g.record_in_rankings()]
QUAL_AVERAGE_YEARS = [y for y, g in _REGISTRY.items() if g.qual_average_in_rankings()]


@pytest.mark.parametrize("year", NO_RECORD_YEARS)
def test_record_in_rankings_false(year: int) -> None:
    assert _REGISTRY[year].record_in_rankings() is False


@pytest.mark.parametrize("year", RECORD_YEARS)
def test_record_in_rankings_true(year: int) -> None:
    assert _REGISTRY[year].record_in_rankings() is True


@pytest.mark.parametrize("year", QUAL_AVERAGE_YEARS)
def test_qual_average_in_rankings_true(year: int) -> None:
    assert _REGISTRY[year].qual_average_in_rankings() is True


def test_qual_average_only_2015() -> None:
    assert QUAL_AVERAGE_YEARS == [2015]


@pytest.mark.parametrize("year", [y for y in _REGISTRY if y != 2015])
def test_qual_average_in_rankings_false(year: int) -> None:
    assert _REGISTRY[year].qual_average_in_rankings() is False


@pytest.mark.parametrize("year", SORT_ORDER_INFO.keys())
def test_ranking_sort_order_info(year: int) -> None:
    assert get_game(year).ranking_sort_order_info() == SORT_ORDER_INFO[year]


def test_ranking_sort_order_info_unsupported() -> None:
    # Year not in registry returns None from the DefaultGame
    assert get_game(1999).ranking_sort_order_info() is None
