from typing import Dict

from backend.common.game_specific.base import SeasonGameConfig
from backend.common.game_specific.seasons.default import DefaultGame
from backend.common.game_specific.seasons.game_specifics_2006 import GameSpecifics2006
from backend.common.game_specific.seasons.game_specifics_2007 import GameSpecifics2007
from backend.common.game_specific.seasons.game_specifics_2008 import GameSpecifics2008
from backend.common.game_specific.seasons.game_specifics_2009 import GameSpecifics2009
from backend.common.game_specific.seasons.game_specifics_2010 import GameSpecifics2010
from backend.common.game_specific.seasons.game_specifics_2011 import GameSpecifics2011
from backend.common.game_specific.seasons.game_specifics_2012 import GameSpecifics2012
from backend.common.game_specific.seasons.game_specifics_2013 import GameSpecifics2013
from backend.common.game_specific.seasons.game_specifics_2014 import GameSpecifics2014
from backend.common.game_specific.seasons.game_specifics_2015 import GameSpecifics2015
from backend.common.game_specific.seasons.game_specifics_2016 import GameSpecifics2016
from backend.common.game_specific.seasons.game_specifics_2017 import GameSpecifics2017
from backend.common.game_specific.seasons.game_specifics_2018 import GameSpecifics2018
from backend.common.game_specific.seasons.game_specifics_2019 import GameSpecifics2019
from backend.common.game_specific.seasons.game_specifics_2020 import GameSpecifics2020
from backend.common.game_specific.seasons.game_specifics_2021 import GameSpecifics2021
from backend.common.game_specific.seasons.game_specifics_2022 import GameSpecifics2022
from backend.common.game_specific.seasons.game_specifics_2023 import GameSpecifics2023
from backend.common.game_specific.seasons.game_specifics_2024 import GameSpecifics2024
from backend.common.game_specific.seasons.game_specifics_2025 import GameSpecifics2025
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026
from backend.common.models.keys import Year

_REGISTRY: Dict[Year, SeasonGameConfig] = {
    2006: GameSpecifics2006(),
    2007: GameSpecifics2007(),
    2008: GameSpecifics2008(),
    2009: GameSpecifics2009(),
    2010: GameSpecifics2010(),
    2011: GameSpecifics2011(),
    2012: GameSpecifics2012(),
    2013: GameSpecifics2013(),
    2014: GameSpecifics2014(),
    2015: GameSpecifics2015(),
    2016: GameSpecifics2016(),
    2017: GameSpecifics2017(),
    2018: GameSpecifics2018(),
    2019: GameSpecifics2019(),
    2020: GameSpecifics2020(),
    2021: GameSpecifics2021(),
    2022: GameSpecifics2022(),
    2023: GameSpecifics2023(),
    2024: GameSpecifics2024(),
    2025: GameSpecifics2025(),
    2026: GameSpecifics2026(),
}

_DEFAULT_GAME: SeasonGameConfig = DefaultGame()


def get_game(year: Year) -> SeasonGameConfig:
    """Returns the SeasonGameConfig for the given year, or a no-op default."""
    return _REGISTRY.get(year, _DEFAULT_GAME)
