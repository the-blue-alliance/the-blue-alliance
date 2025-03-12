from typing import Dict, NotRequired, TypedDict

from backend.common.models.keys import EventKey, TeamKey


class TeamRegionalPoolAdvancement(TypedDict):
    cmp: bool
    cmp_event: NotRequired[EventKey]


RegionalPoolAdvancement = Dict[TeamKey, TeamRegionalPoolAdvancement]
