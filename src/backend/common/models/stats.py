import enum
from typing import Dict

from backend.common.models.keys import TeamId


TStatMap = Dict[TeamId, float]


@enum.unique
class StatType(str, enum.Enum):
    OPR = "oprs"
    DPR = "dprs"
    CCWM = "ccwms"

    # 2016 specific stats
    STRONGHOLD_AUTO_OPR = "2016autoPointsOPR"
    STRONGHOLD_BOULDER_OPR = "2016bouldersOPR"
    STRONGHOLD_CROSS_OPR = "2016crossingsOPR"


EventMatchStats = Dict[StatType, TStatMap]
