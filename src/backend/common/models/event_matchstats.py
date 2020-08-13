import enum
from typing import Dict, Union

from typing_extensions import TypedDict

from backend.common.models.keys import TeamId, TeamKey

Component = str
TeamStatMap = Dict[Union[TeamKey, TeamId], float]


class EventMatchstats(TypedDict):
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
