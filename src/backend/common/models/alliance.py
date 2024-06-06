import enum
from typing import List, Optional, TypedDict

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import DoubleElimRound, PlayoffType
from backend.common.consts.string_enum import StrEnum
from backend.common.models.keys import TeamKey
from backend.common.models.wlt import WLTRecord


@enum.unique
class PlayoffOutcome(StrEnum):
    WON = "won"
    ELIMINATED = "eliminated"
    PLAYING = "playing"


class _EventTeamStatusPlayoffOptional(TypedDict, total=False):
    playoff_type: PlayoffType

    # Relevant for double elim tournaments
    double_elim_round: Optional[DoubleElimRound]

    # Relevant for round robin tournaments
    round_robin_rank: Optional[int]
    advanced_to_round_robin_finals: Optional[bool]

    # Relevant for 2015 tournaments
    playoff_average: Optional[float]


class PlayoffAllianceStatus(_EventTeamStatusPlayoffOptional, total=True):
    level: CompLevel
    current_level_record: Optional[WLTRecord]
    record: Optional[WLTRecord]
    status: PlayoffOutcome


EventAllianceBackup = TypedDict("EventAllianceBackup", {"in": str, "out": str})


class _EventAllianceOptional(TypedDict, total=False):
    declines: List[TeamKey]
    name: str
    backup: EventAllianceBackup
    status: PlayoffAllianceStatus


class EventAlliance(_EventAllianceOptional, total=True):
    picks: List[TeamKey]


class _MatchAllianceOptional(TypedDict, total=False):
    surrogates: List[TeamKey]
    dqs: List[TeamKey]


class MatchAlliance(_MatchAllianceOptional, total=True):
    teams: List[TeamKey]
    score: int
