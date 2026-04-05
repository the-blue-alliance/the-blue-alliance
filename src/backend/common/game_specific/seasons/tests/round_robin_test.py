import pytest

from backend.common.game_specific.registry import get_game

_ROUND_ROBIN_YEARS = {
    2017: {
        "keys": ["totalPoints"],
        "names": ["Match Points"],
    },
    2018: {
        "keys": ["endgamePoints", "autoPoints"],
        "names": ["Park/Climb Points", "Auto Points"],
    },
    2019: {
        "keys": ["cargoPoints", "hatchPanelPoints"],
        "names": ["Cargo Points", "Hatch Panel Points"],
    },
    2020: {
        "keys": [],
        "names": [],
    },
    2021: {
        "keys": [],
        "names": [],
    },
    2022: {
        "keys": ["endgamePoints", "autoPoints"],
        "names": ["Hangar Points", "Auto Taxi/Cargo Points"],
    },
}


@pytest.mark.parametrize("year", _ROUND_ROBIN_YEARS.keys())
def test_round_robin_tiebreak_keys(year: int) -> None:
    assert (
        get_game(year).round_robin_tiebreak_keys() == _ROUND_ROBIN_YEARS[year]["keys"]
    )


@pytest.mark.parametrize("year", _ROUND_ROBIN_YEARS.keys())
def test_round_robin_tiebreaker_names(year: int) -> None:
    assert (
        get_game(year).round_robin_tiebreaker_names()
        == _ROUND_ROBIN_YEARS[year]["names"]
    )


@pytest.mark.parametrize("year", _ROUND_ROBIN_YEARS.keys())
def test_round_robin_lists_same_length(year: int) -> None:
    game = get_game(year)
    assert len(game.round_robin_tiebreak_keys()) == len(
        game.round_robin_tiebreaker_names()
    )


@pytest.mark.parametrize("year", [2016, 2023, 2024, 2025, 2026])
def test_no_round_robin_non_rr_years(year: int) -> None:
    game = get_game(year)
    assert game.round_robin_tiebreak_keys() == []
    assert game.round_robin_tiebreaker_names() == []
