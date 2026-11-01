"""The stored and served form of a match prediction."""

from typing import Literal, Optional

from backend.common.helpers.predictions_v2.model.bonus import BONUS_RP_FIELDS
from backend.common.helpers.predictions_v2.model.types import (
    MatchPrediction,
    RankingPointsPrediction,
    ScoreDistribution,
)
from backend.common.models.event_predictions_v2 import (
    AlliancePredictionV2,
    MatchPredictionV2,
    RankingPointsPredictionV2,
    ScorePredictionV2,
)
from backend.common.models.keys import Year

PredictionKind = Literal["pre_match", "forecast"]


def score_prediction(score: ScoreDistribution) -> ScorePredictionV2:
    return ScorePredictionV2(
        mean=round(score.mean, 2),
        sd=round(score.sd, 2),
        p10=score.quantile(0.1),
        p50=score.quantile(0.5),
        p90=score.quantile(0.9),
    )


def ranking_points_prediction(
    rp: Optional[RankingPointsPrediction], year: Year
) -> Optional[RankingPointsPredictionV2]:
    if rp is None:
        return None
    fields = BONUS_RP_FIELDS.get(year, ())
    bonus = {}
    for key, prob in rp.bonus_rp_probs.items():
        i = int(key.split("_")[1]) - 1
        if i < len(fields):
            bonus[fields[i]] = round(prob, 4)
    return RankingPointsPredictionV2(
        expected_rp=round(rp.expected_rp, 4),
        median_rp=rp.median_rp,
        win_rp_prob=round(rp.win_rp_prob, 4),
        bonus_rp_probs=bonus,
    )


def match_prediction(
    pred: MatchPrediction, year: Year, kind: PredictionKind
) -> MatchPredictionV2:
    return MatchPredictionV2(
        kind=kind,
        red_win_prob=round(pred.red_win_prob, 4),
        red=AlliancePredictionV2(
            score=score_prediction(pred.red_score),
            ranking_points=ranking_points_prediction(pred.red_rp, year),
        ),
        blue=AlliancePredictionV2(
            score=score_prediction(pred.blue_score),
            ranking_points=ranking_points_prediction(pred.blue_rp, year),
        ),
    )
