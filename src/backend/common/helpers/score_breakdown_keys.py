from backend.common.game_specific.registry import get_game
from backend.common.models.keys import Year


class ScoreBreakdownKeys:
    @staticmethod
    def get_valid_score_breakdown_keys(year: Year) -> set[str]:
        """
        Return all valid score breakdown keys for the given year.
        Valid breakdown keys for each season are defined in the corresponding
        SeasonGameConfig subclass (game_specific/seasons/game_specifics_NNNN.py).
        """
        return get_game(year).valid_score_breakdown_keys()
