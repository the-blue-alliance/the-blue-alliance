import enum
from typing import Dict

from backend.common.consts.string_enum import StrEnum
from backend.common.models.keys import TeamId


TStatMap = Dict[TeamId, float]


@enum.unique
class StatType(StrEnum):
    OPR = "oprs"
    DPR = "dprs"
    CCWM = "ccwms"


EventMatchStats = Dict[StatType, TStatMap]
