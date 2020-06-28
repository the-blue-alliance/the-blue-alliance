import enum
from typing import Dict, List


@enum.unique
class CompLevel(enum.Enum):
    QM = "qm"
    EF = "ef"
    QF = "qf"
    SF = "sf"
    F = "f"


COMP_LEVELS: List[CompLevel] = [e for e in CompLevel]

ELIM_LEVELS: List[CompLevel] = [e for e in CompLevel if e != CompLevel.QM]


COMP_LEVELS_VERBOSE: Dict[CompLevel, str] = {
    CompLevel.QM: "Quals",
    CompLevel.QM: "Quals",
    CompLevel.EF: "Eighths",
    CompLevel.QF: "Quarters",
    CompLevel.SF: "Semis",
    CompLevel.F: "Finals",
}


COMP_LEVELS_VERBOSE_FULL: Dict[CompLevel, str] = {
    CompLevel.QM: "Qualification",
    CompLevel.EF: "Octo-finals",
    CompLevel.QF: "Quarterfinals",
    CompLevel.SF: "Semifinals",
    CompLevel.F: "Finals",
}


COMP_LEVELS_PLAY_ORDER: Dict[CompLevel, int] = {
    CompLevel.QM: 1,
    CompLevel.EF: 2,
    CompLevel.QF: 3,
    CompLevel.SF: 4,
    CompLevel.F: 5,
}
