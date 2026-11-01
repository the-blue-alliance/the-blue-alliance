from backend.common.helpers.predictions_v2.model.predictor import HKFPredictor
from backend.common.helpers.predictions_v2.payload import match_prediction
from backend.common.helpers.tests.predictions_v2.model.golden import load_golden


def test_match_prediction_payload() -> None:
    golden = [m for m in load_golden() if m.year == 2016][:60]
    model = HKFPredictor()
    model.start_season(2016)
    for m in golden[:-1]:
        model.update(m.context, m.outcome)
    last = golden[-1]
    assert last.context.is_qual
    payload = match_prediction(model.predict_match(last.context), 2016, "pre_match")

    assert payload["kind"] == "pre_match"
    assert 0.0 <= payload["red_win_prob"] <= 1.0
    for alliance in (payload["red"], payload["blue"]):
        score = alliance["score"]
        assert score["p10"] <= score["p50"] <= score["p90"]
        assert score["sd"] > 0.0
        rp = alliance["ranking_points"]
        assert rp is not None
        assert set(rp["bonus_rp_probs"]) == {
            "teleopDefensesBreached",
            "teleopTowerCaptured",
        }
        assert 0.0 <= rp["expected_rp"] <= 4.0


def test_playoff_payload_has_no_ranking_points() -> None:
    golden = [m for m in load_golden() if m.year == 2016]
    playoff = next(m for m in golden if not m.context.is_qual)
    model = HKFPredictor()
    model.start_season(2016)
    payload = match_prediction(model.predict_match(playoff.context), 2016, "forecast")
    assert payload["kind"] == "forecast"
    assert payload["red"]["ranking_points"] is None
    assert payload["blue"]["ranking_points"] is None
