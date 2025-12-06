from typing import TypedDict

from backend.common.models.keys import TeamKey


class TeamDistrictAdvancement(TypedDict):
    dcmp: bool
    cmp: bool


DistrictAdvancement = dict[TeamKey, TeamDistrictAdvancement]
