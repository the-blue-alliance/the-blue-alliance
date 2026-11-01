from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_predictions_v2 import EventPredictionsV2
from backend.common.queries.event_predictions_v2_query import EventPredictionsV2Query


def test_not_found() -> None:
    assert EventPredictionsV2Query(event_key="2024casj").fetch() is None


def test_found_and_converted() -> None:
    EventPredictionsV2(
        id="2024casj", model_version="hkf-1", forecast_only=True, matches={}
    ).put()
    result = EventPredictionsV2Query(event_key="2024casj").fetch()
    assert result is not None and result.key_name == "2024casj"

    d = EventPredictionsV2Query(event_key="2024casj").fetch_dict(ApiMajorVersion.API_V3)
    assert d is not None
    assert d["event_key"] == "2024casj"
    assert d["model_version"] == "hkf-1"
    assert d["forecast_only"] is True
    assert d["matches"] == {}
    assert isinstance(d["last_updated"], int)
