from typing import Dict, TypedDict

from backend.common.models.keys import TeamKey


class TeamRegionalPoolAdvancement(TypedDict):
    cmp: bool


RegionalPoolAdvancement = Dict[TeamKey, TeamRegionalPoolAdvancement]
