from typing import Dict, TypedDict

from backend.common.models.keys import TeamKey

TeamStatMap = Dict[TeamKey, float]
Component = str
EventComponentOPRs = Dict[Component, TeamStatMap]


class EventMatchstats(TypedDict):
    oprs: TeamStatMap
    dprs: TeamStatMap
    ccwms: TeamStatMap
