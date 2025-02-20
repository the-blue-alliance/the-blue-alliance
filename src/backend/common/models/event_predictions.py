from typing import Dict, List, Literal, NamedTuple, Optional, TypedDict

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.keys import MatchKey, TeamKey


class TComputedMatchInfo(TypedDict):
    mean: Dict[TeamKey, float]
    var: Dict[TeamKey, float]


TQualPlayoff = Literal["qual", "playoff"]
TStatMeanVar = Dict[str, TComputedMatchInfo]


class MatchPrediction(TypedDict):
    blue: Dict
    red: Dict
    winning_alliance: AllianceColor
    prob: float


class MatchPredictionStatsLevel(TypedDict):
    wl_accuracy: Optional[float]
    wl_accuracy_75: Optional[float]
    err_mean: Optional[float]
    err_var: Optional[float]
    brier_scores: Dict[Literal["win_loss"], float]


class TRankingPredictionStats(TypedDict):
    last_played_match: Optional[str]


class TRankingPrediction(NamedTuple):
    avg_rank: int
    min_rank: int
    median_rank: int
    max_rank: int
    avg_rp: float
    min_rp: int
    max_rp: int


TMatchPredictions = Dict[TQualPlayoff, Dict[MatchKey, MatchPrediction]]
TMatchPredictionStats = Dict[TQualPlayoff, MatchPredictionStatsLevel]
TEventStatMeanVars = Dict[TQualPlayoff, TStatMeanVar]
TRankingPredictions = List


class EventPredictions(TypedDict):
    match_predictions: Optional[TMatchPredictions]
    match_prediction_stats: Optional[TMatchPredictionStats]
    stat_mean_vars: Optional[TEventStatMeanVars]
    ranking_predictions: Optional[TRankingPredictions]
    ranking_prediction_stats: Optional[TRankingPredictionStats]
