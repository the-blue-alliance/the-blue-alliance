import math

from backend.common.helpers.predictions_v2.adapter import build_stream, EntryKind
from backend.common.helpers.predictions_v2.backtest import evaluate, replay, v1_metrics
from backend.common.helpers.tests.predictions_v2.api_fixture import load_api_fixture


def test_backtest_scores_the_training_entries() -> None:
    events, matches = load_api_fixture()
    early = {k: e for k, e in events.items() if e.year <= 2017}
    stream = build_stream(early, matches)
    metrics = evaluate(stream, score_years={2017})

    assert set(metrics) == {2017}
    m = metrics[2017]
    assert m.win.matches == sum(1 for it in stream if it.year == 2017)
    assert 0.0 < m.win.brier < 0.25
    assert 0.5 < m.win.accuracy <= 1.0
    assert m.win.log_loss > 0.0
    assert 0.0 < m.score_mae < 100.0
    assert m.rp_brier is not None and 0.0 < m.rp_brier < 0.25


def test_forecast_entries_are_predicted_but_not_learned() -> None:
    events, matches = load_api_fixture()
    stream = build_stream({k: e for k, e in events.items() if e.year == 2016}, matches)
    trained = replay(stream)
    forecast = [
        type(it)(EntryKind.FORECAST, it.slot, it.context, it.outcome, it.fingerprint)
        for it in stream
    ]
    untrained = replay(forecast)
    assert trained.n > 0 and trained.season == 2016
    # Forecast-only entries neither train the model nor roll it over into their season.
    assert untrained.n == 0
    assert untrained.season is None
    assert untrained.teams == {}


def test_v1_comparison_uses_the_same_matches() -> None:
    events, matches = load_api_fixture()
    event_key = "2024orore"
    keys = {m.key_name for m in matches if m.event_key_name == event_key}
    assert keys
    v1 = v1_metrics({event_key: events[event_key]}, matches, keys)
    assert v1.matches == len(keys)
    assert 0.0 < v1.brier < 0.5
    assert not math.isnan(v1.log_loss)
