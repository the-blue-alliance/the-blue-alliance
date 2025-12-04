import enum
from typing import NotRequired, TypedDict

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


class PlayoffAllianceStatus(TypedDict):
    level: CompLevel
    current_level_record: WLTRecord | None
    record: WLTRecord | None
    status: PlayoffOutcome

    playoff_type: NotRequired[PlayoffType]

    # Relevant for double elim tournaments
    double_elim_round: NotRequired[DoubleElimRound | None]

    # Relevant for round robin tournaments
    round_robin_rank: NotRequired[int | None]
    advanced_to_round_robin_finals: NotRequired[bool | None]

    # Relevant for 2015 tournaments
    playoff_average: NotRequired[float | None]


EventAllianceBackup = TypedDict("EventAllianceBackup", {"in": str, "out": str})


class EventAlliance(TypedDict):
    picks: list[TeamKey]
    declines: NotRequired[list[TeamKey]]
    name: NotRequired[str]
    backup: NotRequired[EventAllianceBackup]
    status: NotRequired[PlayoffAllianceStatus]


class MatchAlliance(TypedDict):
    teams: list[TeamKey]
    score: int
    surrogates: NotRequired[list[TeamKey]]
    dqs: NotRequired[list[TeamKey]]
