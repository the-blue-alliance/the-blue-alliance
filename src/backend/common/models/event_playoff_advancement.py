from typing import List, Literal, Mapping, NamedTuple, Optional, TypedDict, Union

from backend.common.consts.alliance_color import AllianceColor, TMatchWinner
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import DoubleElimRound
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, TeamNumber


class BracketItem(TypedDict):
    red_alliance: List[TeamNumber]
    blue_alliance: List[TeamNumber]
    winning_alliance: Optional[TMatchWinner]
    red_wins: int
    blue_wins: int
    red_record: WLTRecord
    blue_record: WLTRecord
    red_name: Optional[str]
    blue_name: Optional[str]


class PlayoffAdvancement2015(NamedTuple):
    complete_alliance: List[TeamNumber]
    scores: List[int]
    average_score: float
    num_played: int


class PlayoffAdvancementRoundRobin(NamedTuple):
    complete_alliance: List[TeamNumber]
    champ_points: List[int]
    sum_champ_points: int
    tiebreaker1: List[int]
    sum_tiebreaker1: int
    tiebreaker2: List[int]
    sum_tiebreaker2: int
    alliance_name: str
    record: WLTRecord


class PlayoffAdvancementDoubleElimAlliance(TypedDict):
    complete_alliance: List[TeamNumber]
    alliance_name: str
    record: WLTRecord
    eliminated: bool


class PlayoffAdvancementDoubleElimRound(NamedTuple):
    competing_alliances: List[PlayoffAdvancementDoubleElimAlliance]
    complete: bool


class PlayoffAdvancementRoundRobinLevels(TypedDict):
    sf: List[PlayoffAdvancementRoundRobin]
    sf_complete: bool


TPlayoffAdvancement2015Levels = Mapping[CompLevel, List[PlayoffAdvancement2015]]


class PlayoffAdvancementDoubleElimLevels(TypedDict):
    rounds: Mapping[DoubleElimRound, PlayoffAdvancementDoubleElimRound]


TBracketTable = Mapping[CompLevel, Mapping[str, BracketItem]]

TPlayoffAdvancement = Union[
    TPlayoffAdvancement2015Levels,
    PlayoffAdvancementRoundRobinLevels,
    PlayoffAdvancementDoubleElimLevels,
]


class EventPlayoffAdvancement(TypedDict):
    """
    This is what is stored in EventDetails
    """

    bracket: TBracketTable
    advancement: Optional[TPlayoffAdvancement]


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
    team_keys: List[TeamKey]
    alliance_name: str
    matches_played: int
    sort_orders: List  # TODO
    extra_stats: List  # TODO


class ApiPlayoffAdvancement(TypedDict):
    """
    This is what's returned in APIv3
    """

    level: str  # comp level + series
    level_name: str
    rankings: Optional[List[ApiPlayoffAdvancementAllianceRank]]
    type: str
    sort_order_info: List[ApiPlayoffAdvancemnetSortOrderInfo]
    extra_stats_info: List[ApiPlayoffAdvancemnetSortOrderInfo]
