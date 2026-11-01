from backend.common.sitevars.predictions_v2_config import PredictionsV2Config


def test_key() -> None:
    assert PredictionsV2Config.key() == "predictions_v2_config"


def test_disabled_by_default() -> None:
    assert PredictionsV2Config.get() == {"enabled": False}
    assert PredictionsV2Config.enabled() is False


def test_enabled() -> None:
    PredictionsV2Config.put({"enabled": True})
    assert PredictionsV2Config.enabled() is True
