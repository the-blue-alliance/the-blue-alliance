from typing import Literal, NamedTuple, TypedDict

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.keys import MatchKey, TeamKey


class TComputedMatchInfo(TypedDict):
    mean: dict[TeamKey, float]
    var: dict[TeamKey, float]


TQualPlayoff = Literal["qual", "playoff"]
TStatMeanVar = dict[str, TComputedMatchInfo]


class MatchPrediction(TypedDict):
    blue: dict  # TODO: Add better typehints, if possible
    red: dict  # TODO: Add better typehints, if possible
    winning_alliance: AllianceColor
    prob: float


class MatchPredictionStatsLevel(TypedDict):
    wl_accuracy: float | None
    wl_accuracy_75: float | None
    err_mean: float | None
    err_var: float | None
    brier_scores: dict[Literal["win_loss"], float]


class TRankingPredictionStats(TypedDict):
    last_played_match: str | None


class TRankingPrediction(NamedTuple):
    avg_rank: int
    min_rank: int
    median_rank: int
    max_rank: int
    avg_rp: float
    min_rp: int
    max_rp: int


TMatchPredictions = dict[TQualPlayoff, dict[MatchKey, MatchPrediction]]
TMatchPredictionStats = dict[TQualPlayoff, MatchPredictionStatsLevel]
TEventStatMeanVars = dict[TQualPlayoff, TStatMeanVar]
TRankingPredictions = list  # TODO: Add better typehints if possible


class EventPredictions(TypedDict):
    match_predictions: TMatchPredictions | None
    match_prediction_stats: TMatchPredictionStats | None
    stat_mean_vars: TEventStatMeanVars | None
    ranking_predictions: TRankingPredictions | None
    ranking_prediction_stats: TRankingPredictionStats | None
