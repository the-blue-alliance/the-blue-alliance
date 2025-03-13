import enum
from typing import Dict, NotRequired, Optional, TypedDict

from backend.common.models.keys import EventKey, TeamKey


@enum.unique
class ChampionshipStatus(enum.IntEnum):
    NOT_INVITED = 0
    PRE_QUALIFIED = 1
    EVENT_QUALIFIED = 2
    POOL_QUALIFIED = 3

    @classmethod
    def from_api_string(cls, api_str: str) -> Optional["ChampionshipStatus"]:
        match api_str:
            case "NotInvited":
                return cls.NOT_INVITED
            case "PreQualified":
                return cls.PRE_QUALIFIED
            case "EventQualified":
                return cls.EVENT_QUALIFIED
            case "PoolQualified":
                return cls.POOL_QUALIFIED
        return None


class TeamRegionalPoolAdvancement(TypedDict):
    cmp: bool
    cmp_status: ChampionshipStatus
    qualifying_event: NotRequired[EventKey]
    qualifying_award_name: NotRequired[str]
    qualifying_pool_week: NotRequired[int]


RegionalPoolAdvancement = Dict[TeamKey, TeamRegionalPoolAdvancement]
