import enum

from backend.common.consts.string_enum import StrEnum
from backend.common.models.keys import TeamId


TStatMap = dict[TeamId, float]


@enum.unique
class StatType(StrEnum):
    OPR = "oprs"
    DPR = "dprs"
    CCWM = "ccwms"


EventMatchStats = dict[StatType, TStatMap]
