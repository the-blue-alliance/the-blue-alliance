from typing import Any, TypedDict


class EventPredictions(TypedDict):
    match_predictions: Any
    match_prediction_stats: Any
    stat_mean_vars: Any
    ranking_predictions: Any
    ranking_prediction_stats: Any
