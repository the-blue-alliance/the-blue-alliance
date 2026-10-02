from backend.common.game_specific.registry import get_game
from backend.common.game_specific.seasons.default import DefaultGame
from backend.common.game_specific.seasons.game_specifics_2010 import GameSpecifics2010
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026


def test_get_game_returns_registered_season() -> None:
    assert isinstance(get_game(2010), GameSpecifics2010)
    assert isinstance(get_game(2026), GameSpecifics2026)


def test_get_game_returns_default_for_unknown_year() -> None:
    assert isinstance(get_game(1999), DefaultGame)


def _counter_names(year: int) -> set[str]:
    return {c.name for c in get_game(year).success_rate_counters()}


def test_auto_win_conversion_tracked_by_every_modern_season() -> None:
    for year in [*range(2016, 2021), *range(2022, 2027)]:
        assert "auto_win_conversion" in _counter_names(year), year


def test_auto_win_conversion_untracked_by_2015_and_2021() -> None:
    assert _counter_names(2015) == set()
    assert _counter_names(2021) == set()
