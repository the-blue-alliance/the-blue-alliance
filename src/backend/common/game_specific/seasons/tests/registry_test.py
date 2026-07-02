from backend.common.game_specific.registry import get_game
from backend.common.game_specific.seasons.default import DefaultGame
from backend.common.game_specific.seasons.game_specifics_2010 import GameSpecifics2010
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026


def test_get_game_returns_registered_season() -> None:
    assert isinstance(get_game(2010), GameSpecifics2010)
    assert isinstance(get_game(2026), GameSpecifics2026)


def test_get_game_returns_default_for_unknown_year() -> None:
    assert isinstance(get_game(1999), DefaultGame)
