import enum
from typing import Dict

from backend.common.models.keys import TeamId


Component = str
TStatMap = Dict[TeamId, float]


@enum.unique
class StatType(str, enum.Enum):
    OPR = "oprs"
    DPR = "dprs"
    CCWM = "ccwms"
    COPR = "coprs"


EventMatchStats = Dict[StatType, TStatMap]
