from collections.abc import Mapping
from typing import Literal, NamedTuple, TypedDict

from backend.common.consts.alliance_color import AllianceColor, TMatchWinner
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import DoubleElimRound
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, TeamNumber


class BracketItem(TypedDict):
    red_alliance: list[TeamNumber]
    blue_alliance: list[TeamNumber]
    winning_alliance: TMatchWinner | None
    red_wins: int
    blue_wins: int
    red_record: WLTRecord
    blue_record: WLTRecord
    red_name: str | None
    blue_name: str | None


class PlayoffAdvancement2015(NamedTuple):
    complete_alliance: list[TeamNumber]
    scores: list[int]
    average_score: float
    num_played: int


class PlayoffAdvancementRoundRobin(NamedTuple):
    complete_alliance: list[TeamNumber]
    champ_points: list[int]
    sum_champ_points: int
    tiebreaker1: list[int]
    sum_tiebreaker1: int
    tiebreaker2: list[int]
    sum_tiebreaker2: int
    alliance_name: str
    record: WLTRecord


class PlayoffAdvancementDoubleElimAlliance(TypedDict):
    complete_alliance: list[TeamNumber]
    alliance_name: str
    record: WLTRecord
    eliminated: bool


class PlayoffAdvancementDoubleElimRound(NamedTuple):
    competing_alliances: list[PlayoffAdvancementDoubleElimAlliance]
    complete: bool


class PlayoffAdvancementRoundRobinLevels(TypedDict):
    sf: list[PlayoffAdvancementRoundRobin]
    sf_complete: bool


TPlayoffAdvancement2015Levels = Mapping[CompLevel, list[PlayoffAdvancement2015]]


class PlayoffAdvancementDoubleElimLevels(TypedDict):
    rounds: Mapping[DoubleElimRound, PlayoffAdvancementDoubleElimRound]


TBracketTable = Mapping[CompLevel, Mapping[str, BracketItem]]

TPlayoffAdvancement = (
    TPlayoffAdvancement2015Levels
    | PlayoffAdvancementRoundRobinLevels
    | PlayoffAdvancementDoubleElimLevels
)


class EventPlayoffAdvancement(TypedDict):
    """
    This is what is stored in EventDetails
    """

    bracket: TBracketTable
    advancement: TPlayoffAdvancement | None


class ApiPlayoffAdvancemnetSortOrderInfo(TypedDict):
    name: str
    type: Literal["int", "bool"]
    precision: int


class _ApiPlayoffAdvancemnetAllianceRankOptional(TypedDict, total=False):
    alliance_color: AllianceColor
    rank: int
    record: WLTRecord


class ApiPlayoffAdvancementAllianceRank(
    _ApiPlayoffAdvancemnetAllianceRankOptional, total=True
):
    team_keys: list[TeamKey]
    alliance_name: str
    matches_played: int
    sort_orders: list  # TODO: Add proper typehints here
    extra_stats: list  # TODO: Add proper typehints here


class ApiPlayoffAdvancement(TypedDict):
    """
    This is what's returned in APIv3
    """

    level: str  # comp level + series
    level_name: str
    rankings: list[ApiPlayoffAdvancementAllianceRank] | None
    type: str
    sort_order_info: list[ApiPlayoffAdvancemnetSortOrderInfo]
    extra_stats_info: list[ApiPlayoffAdvancemnetSortOrderInfo]
