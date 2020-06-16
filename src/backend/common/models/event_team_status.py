import enum
from typing import List, Optional

from typing_extensions import TypedDict


@enum.unique
class EventTeamLevelStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    PLAYING = "playing"
    COMPLETED = "completed"


@enum.unique
class EventTeamPlayoffStatus(str, enum.Enum):
    WON = "won"
    ELIMINATED = "eliminated"
    PLAYING = "playing"


@enum.unique
class ElimCompLevel(str, enum.Enum):
    EF = "ef"
    QF = "qf"
    SF = "sf"
    F = "f"


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
    num_teams: int
    sort_orders: Optional[List[float]]


class EventTeamStatusQual(TypedDict):
    status: EventTeamLevelStatus
    num_teams: int
    ranking: EventTeamRanking
    sort_order_info: List[RankingSortOrderInfo]


class EventTeamStatusPlayoff(TypedDict):
    level: ElimCompLevel
    current_level_record: Optional[WLTRecord]
    record: Optional[WLTRecord]
    status: EventTeamPlayoffStatus
    playoff_average: Optional[float]


EventTeamStatusAllianceBackup = TypedDict(
    "EventTeamStatusAllianceBackup", {"in": str, "out": str}
)


class EventTeamStatusAlliance(TypedDict):
    name: Optional[str]
    number: int
    pick: int
    backup: Optional[EventTeamStatusAllianceBackup]


class EventTeamStatus(TypedDict):
    qual: Optional[EventTeamStatusQual]
    playoff: Optional[EventTeamStatusPlayoff]
    alliance: EventTeamStatusAlliance
    last_match_key: Optional[str]
    next_match_key: Optional[str]
