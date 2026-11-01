import pytest

from backend.common.manipulators.event_predictions_v2_manipulator import (
    EventPredictionsV2Manipulator,
)
from backend.common.models.event_predictions_v2 import (
    EventPredictionsV2,
    MatchPredictionV2,
    ScorePredictionV2,
)
from backend.common.queries.event_predictions_v2_query import EventPredictionsV2Query


@pytest.fixture(autouse=True)
def auto_use_taskqueue_stub(taskqueue_stub) -> None:
    pass


def _prediction(p: float) -> MatchPredictionV2:
    score = ScorePredictionV2(mean=50.0, sd=10.0, p10=37, p50=50, p90=63)
    return MatchPredictionV2(
        kind="pre_match",
        red_win_prob=p,
        red={"score": score, "ranking_points": None},
        blue={"score": score, "ranking_points": None},
    )


def test_create_and_update() -> None:
    EventPredictionsV2Manipulator.createOrUpdate(
        EventPredictionsV2(
            id="2024casj",
            model_version="hkf-1",
            matches={"2024casj_qm1": _prediction(0.6)},
        )
    )
    stored = EventPredictionsV2.get_by_id("2024casj")
    assert stored is not None
    assert stored.matches["2024casj_qm1"]["red_win_prob"] == 0.6
    assert stored.year == 2024

    EventPredictionsV2Manipulator.createOrUpdate(
        EventPredictionsV2(
            id="2024casj",
            model_version="hkf-1",
            forecast_only=False,
            matches={"2024casj_qm1": _prediction(0.7)},
        )
    )
    stored = EventPredictionsV2.get_by_id("2024casj")
    assert stored is not None
    assert stored.matches == {"2024casj_qm1": _prediction(0.7)}


def test_cache_keys() -> None:
    model = EventPredictionsV2(id="2024casj", model_version="hkf-1", matches={})
    model._affected_references["key"].add(model.key)
    keys = EventPredictionsV2Manipulator.getCacheKeysAndQueries(
        model._affected_references
    )
    assert keys == [
        (EventPredictionsV2Query("2024casj").cache_key, EventPredictionsV2Query)
    ]
