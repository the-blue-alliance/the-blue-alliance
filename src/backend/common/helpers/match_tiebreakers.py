from __future__ import annotations

from typing import List

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import (
    AllianceColor,
    TMatchWinner,
)
from backend.common.consts.comp_level import CompLevel, ELIM_LEVELS
from backend.common.game_specific.base import TCriteria
from backend.common.game_specific.registry import get_game
from backend.common.models.match import Match


class MatchTiebreakers(object):
    @classmethod
    def tiebreak_winner(cls, match: Match) -> TMatchWinner:
        """
        Compute elim winner using tiebreakers
        """
        if match.comp_level not in ELIM_LEVELS or match.score_breakdown is None:
            return ""

        if AllianceColor.RED not in none_throws(
            match.score_breakdown
        ) or AllianceColor.BLUE not in none_throws(match.score_breakdown):
            return ""

        red_breakdown = none_throws(match.score_breakdown)[AllianceColor.RED]
        blue_breakdown = none_throws(match.score_breakdown)[AllianceColor.BLUE]

        game = get_game(match.year)

        # Finals matches 1-3 can only be tiebroken when the game explicitly allows it.
        if (
            not game.finals_can_be_tiebroken()
            and match.comp_level == CompLevel.F
            and match.match_number <= 3
        ):
            return ""

        tiebreakers: List[TCriteria] = game.tiebreak_criteria(
            red_breakdown, blue_breakdown
        )

        for tiebreaker in tiebreakers:
            if tiebreaker is None:
                return ""
            elif tiebreaker[0] > tiebreaker[1]:
                return AllianceColor.RED
            elif tiebreaker[1] > tiebreaker[0]:
                return AllianceColor.BLUE
        return ""
