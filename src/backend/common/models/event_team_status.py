import enum
from typing import List, Optional, TypedDict

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.string_enum import StrEnum
from backend.common.models.alliance import EventAllianceBackup
from backend.common.models.keys import TeamKey


@enum.unique
class EventTeamLevelStatus(StrEnum):
    NOT_STARTED = "not_started"
    PLAYING = "playing"
    COMPLETED = "completed"


@enum.unique
class EventTeamPlayoffStatus(StrEnum):
    WON = "won"
    ELIMINATED = "eliminated"
    PLAYING = "playing"


class WLTRecord(TypedDict):
    wins: int
    losses: int
    ties: int


class RankingSortOrderInfo(TypedDict):
    precision: int
    name: str


class EventTeamRanking(TypedDict):
    rank: Optional[int]
    matches_played: int
    dq: Optional[int]
    record: Optional[WLTRecord]
    qual_average: Optional[float]
    sort_orders: Optional[List[float]]
    team_key: TeamKey


class EventTeamStatusQual(TypedDict):
    status: EventTeamLevelStatus
    num_teams: int
    ranking: EventTeamRanking
    sort_order_info: Optional[List[RankingSortOrderInfo]]


class EventTeamStatusPlayoff(TypedDict):
    level: CompLevel
    current_level_record: Optional[WLTRecord]
    record: Optional[WLTRecord]
    status: EventTeamPlayoffStatus
    playoff_average: Optional[float]


class EventTeamStatusAlliance(TypedDict):
    name: Optional[str]
    number: int
    pick: int
    backup: Optional[EventAllianceBackup]


class EventTeamStatus(TypedDict):
    qual: Optional[EventTeamStatusQual]
    playoff: Optional[EventTeamStatusPlayoff]
    alliance: Optional[EventTeamStatusAlliance]
    last_match_key: Optional[str]
    next_match_key: Optional[str]


class EventTeamStatusStrings(TypedDict):
    alliance: Optional[str]
    playoff: Optional[str]
    overall: Optional[str]
