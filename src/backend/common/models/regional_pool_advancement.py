import enum
from typing import Dict, NotRequired, TypedDict

from backend.common.consts.string_enum import StrEnum
from backend.common.models.keys import EventKey, TeamKey


@enum.unique
class ChampionshipStatus(StrEnum):
    NOT_INVITED = "NotInvited"
    PRE_QUALIFIED = "PreQualified"
    EVENT_QUALIFIED = "EventQualified"
    POOL_QUALIFIED = "PoolQualified"
    DECLINED = "Declined"


class TeamRegionalPoolAdvancement(TypedDict):
    cmp: bool
    cmp_status: ChampionshipStatus
    qualifying_event: NotRequired[EventKey]
    qualifying_award_name: NotRequired[str]
    qualifying_pool_week: NotRequired[int]


RegionalPoolAdvancement = Dict[TeamKey, TeamRegionalPoolAdvancement]
