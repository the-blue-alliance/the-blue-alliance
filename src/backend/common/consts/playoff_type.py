from __future__ import annotations

import enum
from typing import Dict, Set, Tuple

from backend.common.consts.comp_level import CompLevel


@enum.unique
class DoubleElimBracket(str, enum.Enum):
    WINNER = "winner"
    LOSER = "loser"


@enum.unique
class PlayoffType(enum.IntEnum):
    # Standard Brackets
    BRACKET_8_TEAM = 0
    BRACKET_16_TEAM = 1
    BRACKET_4_TEAM = 2

    # 2015 is special
    AVG_SCORE_8_TEAM = 3

    # Round Robin
    ROUND_ROBIN_6_TEAM = 4

    # Double Elimination Bracket
    DOUBLE_ELIM_8_TEAM = 5

    # Festival of Champions
    BO5_FINALS = 6
    BO3_FINALS = 7

    # Custom
    CUSTOM = 8


BRACKET_TYPES: Set[PlayoffType] = {
    PlayoffType.BRACKET_8_TEAM,
    PlayoffType.BRACKET_16_TEAM,
    PlayoffType.BRACKET_4_TEAM,
}


DOUBLE_ELIM_TYPES: Set[PlayoffType] = {
    PlayoffType.DOUBLE_ELIM_8_TEAM,
}


# Names for Rendering
TYPE_NAMES: Dict[PlayoffType, str] = {
    PlayoffType.BRACKET_8_TEAM: "Elimination Bracket (8 Alliances)",
    PlayoffType.BRACKET_4_TEAM: "Elimination Bracket (4 Alliances)",
    PlayoffType.BRACKET_16_TEAM: "Elimination Bracket (16 Alliances)",
    PlayoffType.AVG_SCORE_8_TEAM: "Average Score (8 Alliances)",
    PlayoffType.ROUND_ROBIN_6_TEAM: "Round Robin (6 Alliances)",
    PlayoffType.DOUBLE_ELIM_8_TEAM: "Double Elimination Bracket (8 Alliances)",
    PlayoffType.BO3_FINALS: "Best of 3 Finals",
    PlayoffType.BO5_FINALS: "Best of 5 Finals",
    PlayoffType.CUSTOM: "Custom",
}


BRACKET_ELIM_MAPPING: Dict[int, Tuple[int, int]] = {
    1: (1, 1),  # (set, match)
    2: (2, 1),
    3: (3, 1),
    4: (4, 1),
    5: (1, 2),
    6: (2, 2),
    7: (3, 2),
    8: (4, 2),
    9: (1, 3),
    10: (2, 3),
    11: (3, 3),
    12: (4, 3),
    13: (1, 1),
    14: (2, 1),
    15: (1, 2),
    16: (2, 2),
    17: (1, 3),
    18: (2, 3),
    19: (1, 1),
    20: (1, 2),
    21: (1, 3),
    22: (1, 4),
    23: (1, 5),
    24: (1, 6),
}


BRACKET_OCTO_ELIM_MAPPING: Dict[int, Tuple[int, int]] = {
    # octofinals
    1: (1, 1),  # (set, match)
    2: (2, 1),
    3: (3, 1),
    4: (4, 1),
    5: (5, 1),
    6: (6, 1),
    7: (7, 1),
    8: (8, 1),
    9: (1, 2),
    10: (2, 2),
    11: (3, 2),
    12: (4, 2),
    13: (5, 2),
    14: (6, 2),
    15: (7, 2),
    16: (8, 2),
    17: (1, 3),
    18: (2, 3),
    19: (3, 3),
    20: (4, 3),
    21: (5, 3),
    22: (6, 3),
    23: (7, 3),
    24: (8, 3),
    # quarterfinals
    25: (1, 1),
    26: (2, 1),
    27: (3, 1),
    28: (4, 1),
    29: (1, 2),
    30: (2, 2),
    31: (3, 2),
    32: (4, 2),
    33: (1, 3),
    34: (2, 3),
    35: (3, 3),
    36: (4, 3),
    # semifinals
    37: (1, 1),
    38: (2, 1),
    39: (1, 2),
    40: (2, 2),
    41: (1, 3),
    42: (2, 3),
    # finals
    43: (1, 1),
    44: (1, 2),
    45: (1, 3),
    46: (1, 4),
    47: (1, 5),
    48: (1, 6),
}

# Map match number -> set/match for a 8 alliance double elim bracket
# Based off: https://www.printyourbrackets.com/fillable-brackets/8-seeded-double-fillable.pdf
# Matches 1-6 are ef, 7-10 are qf, 11/12 are sf, 13 is f1, and 14/15 are f2
DOUBLE_ELIM_MAPPING: Dict[int, Tuple[CompLevel, int, int]] = {
    # octofinals (winners bracket)
    1: (CompLevel.EF, 1, 1),
    2: (CompLevel.EF, 2, 1),
    3: (CompLevel.EF, 3, 1),
    4: (CompLevel.EF, 4, 1),
    # octofinals (losers bracket)
    5: (CompLevel.EF, 5, 1),
    6: (CompLevel.EF, 6, 1),
    # quarterfinals (winners bracket)
    7: (CompLevel.QF, 1, 1),
    8: (CompLevel.QF, 2, 1),
    # quarterfinals (losers bracket)
    9: (CompLevel.QF, 3, 1),
    10: (CompLevel.QF, 4, 1),
    # semifinals (winners bracket)
    11: (CompLevel.SF, 1, 1),
    # semifinals (losers bracket)
    12: (CompLevel.SF, 2, 1),
    # finals (losers bracket)
    13: (CompLevel.F, 1, 1),
    # overall finals (winners bracket)
    14: (CompLevel.F, 2, 1),
    15: (CompLevel.F, 2, 2),
}
