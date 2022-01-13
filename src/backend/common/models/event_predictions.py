from typing import Any, Dict, Literal, TypedDict

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.keys import MatchKey, TeamKey


TQualPlayoff = Literal["qual", "playoff"]
TStatVarMean = Dict[TeamKey, float]


class _MatchPredictionLevel(TypedDict):
    blue: Dict
    red: Dict
    winning_alliance: AllianceColor
    prob: float


class MatchPredictionStatsLevel(TypedDict):
    wl_accuracy: float
    wl_accuracy_75: float
    err_mean: float
    err_var: float
    brier_scores: Dict[Literal["win_loss"], float]


class EventPredictions(TypedDict, total=False):
    match_predictions: Dict[TQualPlayoff, Dict[MatchKey, _MatchPredictionLevel]]
    match_prediction_stats: Dict[TQualPlayoff, MatchPredictionStatsLevel]
    stat_mean_vars: Dict[TQualPlayoff, Dict[str, TStatVarMean]]
    ranking_predictions: Any
    ranking_prediction_stats: Any
