from typing import Dict, TypedDict

from backend.common.models.keys import TeamKey


class TeamDistrictAdvancement(TypedDict):
    dcmp: bool
    cmp: bool


DistrictAdvancement = Dict[TeamKey, TeamDistrictAdvancement]
