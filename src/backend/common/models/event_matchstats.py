from typing import TypedDict

from backend.common.models.keys import TeamKey

TeamStatMap = dict[TeamKey, float]
Component = str
EventComponentOPRs = dict[Component, TeamStatMap]


class EventMatchstats(TypedDict):
    oprs: TeamStatMap
    dprs: TeamStatMap
    ccwms: TeamStatMap
