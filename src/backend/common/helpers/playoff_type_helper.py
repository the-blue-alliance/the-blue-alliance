from typing import Tuple

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import (
    BRACKET_ELIM_MAPPING,
    BRACKET_OCTO_ELIM_MAPPING,
    DOUBLE_ELIM_4_MAPPING,
    DOUBLE_ELIM_MAPPING,
    DoubleElimRound,
    LEGACY_DOUBLE_ELIM_MAPPING,
    LegacyDoubleElimBracket,
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
            elif playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
                level, _, _ = DOUBLE_ELIM_4_MAPPING[match_number]
                return level
            elif playoff_type == PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM:
                level, _, _ = LEGACY_DOUBLE_ELIM_MAPPING[match_number]
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
                elif playoff_type == PlayoffType.BRACKET_2_TEAM and match_number <= 18:
                    # Account for a 2 team bracket where numbering starts at 1
                    match_number += 18

                if match_number <= 12:
                    return CompLevel.QF
                elif match_number <= 18:
                    return CompLevel.SF
                else:
                    return CompLevel.F

    @classmethod
    def get_comp_level_octo(cls, match_number: int) -> CompLevel:
        """No 2015 support"""
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
            _, set, match = DOUBLE_ELIM_MAPPING[match_number]
            return set, match
        elif playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
            _, set, match = DOUBLE_ELIM_4_MAPPING[match_number]
            return set, match
        elif playoff_type == PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM:
            _, set, match = LEGACY_DOUBLE_ELIM_MAPPING[match_number]
            return set, match
        elif (
            playoff_type == PlayoffType.BO3_FINALS
            or playoff_type == PlayoffType.BO5_FINALS
        ):
            return 1, match_number
        else:
            if playoff_type == PlayoffType.BRACKET_4_TEAM and match_number <= 12:
                match_number += 12
            elif playoff_type == PlayoffType.BRACKET_2_TEAM and match_number <= 18:
                match_number += 18

            return (
                BRACKET_OCTO_ELIM_MAPPING[match_number]
                if playoff_type == PlayoffType.BRACKET_16_TEAM
                else BRACKET_ELIM_MAPPING[match_number]
            )

    # Determine if a match is in the winner or loser bracket
    @classmethod
    def get_double_elim_bracket(
        cls, level: CompLevel, set: int
    ) -> LegacyDoubleElimBracket:
        if level == CompLevel.EF:
            return (
                LegacyDoubleElimBracket.WINNER
                if set <= 4
                else LegacyDoubleElimBracket.LOSER
            )
        elif level == CompLevel.QF:
            return (
                LegacyDoubleElimBracket.WINNER
                if set <= 2
                else LegacyDoubleElimBracket.LOSER
            )
        elif level == CompLevel.SF:
            return (
                LegacyDoubleElimBracket.WINNER
                if set == 1
                else LegacyDoubleElimBracket.LOSER
            )
        elif level == CompLevel.F:
            return (
                LegacyDoubleElimBracket.LOSER
                if set == 1
                else LegacyDoubleElimBracket.WINNER
            )
        raise ValueError(f"Bad CompLevel {level}")

    @classmethod
    def get_double_elim_round_pre_2023(
        cls, level: CompLevel, set: int
    ) -> DoubleElimRound:
        if level == CompLevel.EF and set <= 4:
            return DoubleElimRound.ROUND1
        elif (level == CompLevel.EF and set <= 6) or (
            level == CompLevel.QF and set <= 2
        ):
            return DoubleElimRound.ROUND2
        elif level == CompLevel.QF and set <= 4:
            return DoubleElimRound.ROUND3
        elif level == CompLevel.SF:
            return DoubleElimRound.ROUND4
        elif level == CompLevel.F and set == 1:
            return DoubleElimRound.ROUND5
        elif level == CompLevel.F and set == 2:
            return DoubleElimRound.FINALS
        raise ValueError(f"Bad CompLevel/set: {level} {set}")

    @classmethod
    def get_double_elim_round(cls, level: CompLevel, set: int) -> DoubleElimRound:
        if level == CompLevel.SF and set <= 4:
            return DoubleElimRound.ROUND1
        elif level == CompLevel.SF and set <= 8:
            return DoubleElimRound.ROUND2
        elif level == CompLevel.SF and set <= 10:
            return DoubleElimRound.ROUND3
        elif level == CompLevel.SF and set <= 12:
            return DoubleElimRound.ROUND4
        elif level == CompLevel.SF and set <= 13:
            return DoubleElimRound.ROUND5
        elif level == CompLevel.F:
            return DoubleElimRound.FINALS
        raise ValueError(f"Bad CompLevel/set: {level} {set}")

    @classmethod
    def get_double_elim_4_round(cls, level: CompLevel, set: int) -> DoubleElimRound:
        if level == CompLevel.SF and set <= 2:
            return DoubleElimRound.ROUND1
        elif level == CompLevel.SF and set <= 4:
            return DoubleElimRound.ROUND2
        elif level == CompLevel.SF and set <= 5:
            return DoubleElimRound.ROUND3
        elif level == CompLevel.F:
            return DoubleElimRound.FINALS
        raise ValueError(f"Bad CompLevel/set: {level} {set}")
