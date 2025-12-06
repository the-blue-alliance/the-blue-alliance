import enum
from typing import TypedDict

from backend.common.consts.string_enum import StrEnum
from backend.common.models.alliance import EventAllianceBackup, PlayoffAllianceStatus
from backend.common.models.keys import TeamKey
from backend.common.models.wlt import WLTRecord


@enum.unique
class EventTeamLevelStatus(StrEnum):
    NOT_STARTED = "not_started"
    PLAYING = "playing"
    COMPLETED = "completed"


class RankingSortOrderInfo(TypedDict):
    precision: int
    name: str


class EventTeamRanking(TypedDict):
    rank: int | None
    matches_played: int
    dq: int | None
    record: WLTRecord | None
    qual_average: float | None
    sort_orders: list[float] | None
    team_key: TeamKey


class EventTeamStatusQual(TypedDict):
    status: EventTeamLevelStatus
    num_teams: int
    ranking: EventTeamRanking
    sort_order_info: list[RankingSortOrderInfo] | None


class EventTeamStatusAlliance(TypedDict):
    name: str | None
    number: int
    pick: int
    backup: EventAllianceBackup | None


class EventTeamStatus(TypedDict):
    qual: EventTeamStatusQual | None
    playoff: PlayoffAllianceStatus | None
    alliance: EventTeamStatusAlliance | None
    last_match_key: str | None
    next_match_key: str | None


class EventTeamStatusStrings(TypedDict):
    alliance: str | None
    playoff: str | None
    overall: str | None
