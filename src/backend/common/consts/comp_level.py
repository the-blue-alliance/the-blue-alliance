import enum
from typing import Dict, List

from backend.common.consts.string_enum import StrEnum


@enum.unique
class CompLevel(StrEnum):
    PM = "pm"
    QM = "qm"
    EF = "ef"
    QF = "qf"
    SF = "sf"
    F = "f"

    @staticmethod
    def ndb_validate(_prop, value):
        """
        This function turns an instance of the enum
        into its string value for storage in the db
        See https://cloud.google.com/appengine/docs/standard/python/ndb/entity-property-reference#options
        """
        if isinstance(value, CompLevel):
            return value.value
        return None


COMP_LEVELS: List[CompLevel] = [e.value for e in CompLevel]

ELIM_LEVELS: List[CompLevel] = [
    e.value for e in CompLevel if e not in (CompLevel.PM, CompLevel.QM)
]


COMP_LEVELS_VERBOSE: Dict[CompLevel, str] = {
    CompLevel.PM: "Practice",
    CompLevel.QM: "Quals",
    CompLevel.QM: "Quals",
    CompLevel.EF: "Eighths",
    CompLevel.QF: "Quarters",
    CompLevel.SF: "Semis",
    CompLevel.F: "Finals",
}


COMP_LEVELS_VERBOSE_FULL: Dict[CompLevel, str] = {
    CompLevel.PM: "Practice",
    CompLevel.QM: "Qualification",
    CompLevel.EF: "Octo-finals",
    CompLevel.QF: "Quarterfinals",
    CompLevel.SF: "Semifinals",
    CompLevel.F: "Finals",
}


COMP_LEVELS_PLAY_ORDER: Dict[CompLevel, int] = {
    CompLevel.PM: 0,
    CompLevel.QM: 1,
    CompLevel.EF: 2,
    CompLevel.QF: 3,
    CompLevel.SF: 4,
    CompLevel.F: 5,
}
