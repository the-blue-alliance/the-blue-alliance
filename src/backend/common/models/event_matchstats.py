import enum
from typing import Dict

from typing_extensions import TypedDict

from backend.common.models.keys import TeamKey

Component = str
TeamStatMap = Dict[TeamKey, float]


class EventMatchStats(TypedDict):
    oprs: TeamStatMap
    dprs: TeamStatMap
    ccwms: TeamStatMap
    coprs: Dict[Component, TeamStatMap]


@enum.unique
class StatType(str, enum.Enum):
    OPR = "oprs"
    DPR = "dprs"
    CCWM = "ccwms"
    COPR = "coprs"
