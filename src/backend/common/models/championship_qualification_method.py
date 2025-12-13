import enum
from typing import NotRequired, TypedDict

from backend.common.consts.award_type import AwardType
from backend.common.models.keys import EventKey


@enum.unique
class ChampionshipInviteReason(enum.IntEnum):
    OTHER = 0
    PREQUALIFIED = 1
    WAITLIST = 2

    # Used for DCMP Advancement
    EVENT_WINNING_ALLIANCE_MEMBER = 3
    AWARD_WINNER = 4
    POINT_RANKING = 5

    # Regionals only auto invite captain + first pick
    WINNING_ALLIANCE_CAPTAIN = 6
    WINNING_ALLIANCE_FIRST_PICK = 7


class ChampionshipQualificationMethod(TypedDict):
    invite_reason: ChampionshipInviteReason
    event: NotRequired[EventKey]
    award: NotRequired[AwardType]
