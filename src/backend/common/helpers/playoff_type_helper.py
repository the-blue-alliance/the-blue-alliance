from typing import Tuple

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import (
    BRACKET_ELIM_MAPPING,
    BRACKET_OCTO_ELIM_MAPPING,
    DOUBLE_ELIM_MAPPING,
    DoubleElimBracket,
    PlayoffType,
)


class PlayoffTypeHelper:
    @classmethod
    def get_comp_level(
        cls, playoff_type: PlayoffType, match_level: str, match_number: int
    ) -> CompLevel:
        if match_level == "Qualification":
            return CompLevel.QM
        else:
            if playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
                if match_number <= 8:
                    return CompLevel.QF
                elif match_number <= 14:
                    return CompLevel.SF
                else:
                    return CompLevel.F
            elif playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
                # Einstein 2017 for example. 15 round robin matches, then finals
                return CompLevel.SF if match_number <= 15 else CompLevel.F
            elif playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM:
                level, _, _ = DOUBLE_ELIM_MAPPING[match_number]
                return level
            elif (
                playoff_type == PlayoffType.BO3_FINALS
                or playoff_type == PlayoffType.BO5_FINALS
            ):
                return CompLevel.F
            else:
                if playoff_type == PlayoffType.BRACKET_16_TEAM:
                    return cls.get_comp_level_octo(match_number)
                elif playoff_type == PlayoffType.BRACKET_4_TEAM and match_number <= 12:
                    # Account for a 4 team bracket where numbering starts at 1
                    match_number += 12
                if match_number <= 12:
                    return CompLevel.QF
                elif match_number <= 18:
                    return CompLevel.SF
                else:
                    return CompLevel.F

    @classmethod
    def get_comp_level_octo(cls, match_number: int) -> CompLevel:
        """ No 2015 support """
        if match_number <= 24:
            return CompLevel.EF
        elif match_number <= 36:
            return CompLevel.QF
        elif match_number <= 42:
            return CompLevel.SF
        else:
            return CompLevel.F

    @classmethod
    def get_set_match_number(
        cls, playoff_type: PlayoffType, comp_level: CompLevel, match_number: int
    ) -> Tuple[int, int]:
        if comp_level == CompLevel.QM:
            return 1, match_number

        if playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
            if comp_level == CompLevel.SF:
                return 1, match_number - 8
            elif comp_level == CompLevel.F:
                return 1, match_number - 14
            else:  # qf
                return 1, match_number
        if playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            # Einstein 2017 for example. 15 round robin matches from sf1-1 to sf1-15, then finals
            match_number = match_number if match_number <= 15 else match_number - 15
            if comp_level == CompLevel.F:
                return 1, match_number
            else:
                return 1, match_number
        elif playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM:
            level, set, match = DOUBLE_ELIM_MAPPING[match_number]
            return set, match
        elif (
            playoff_type == PlayoffType.BO3_FINALS
            or playoff_type == PlayoffType.BO5_FINALS
        ):
            return 1, match_number
        else:
            if playoff_type == PlayoffType.BRACKET_4_TEAM and match_number <= 12:
                match_number += 12
            return (
                BRACKET_OCTO_ELIM_MAPPING[match_number]
                if playoff_type == PlayoffType.BRACKET_16_TEAM
                else BRACKET_ELIM_MAPPING[match_number]
            )

    # Determine if a match is in the winner or loser bracket
    @classmethod
    def get_double_elim_bracket(cls, level: CompLevel, set: int) -> DoubleElimBracket:
        if level == CompLevel.EF:
            return DoubleElimBracket.WINNER if set <= 4 else DoubleElimBracket.LOSER
        elif level == CompLevel.QF:
            return DoubleElimBracket.WINNER if set <= 2 else DoubleElimBracket.LOSER
        elif level == CompLevel.SF:
            return DoubleElimBracket.WINNER if set == 1 else DoubleElimBracket.LOSER
        elif level == CompLevel.F:
            return DoubleElimBracket.LOSER if set == 1 else DoubleElimBracket.WINNER
        raise ValueError(f"Bad CompLevel {level}")
