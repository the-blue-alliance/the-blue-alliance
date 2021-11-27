import itertools
from unittest.mock import patch

import pytest

from backend.common.google_analytics import GoogleAnalytics


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


def test_GoogleAnalytics_track_event_missing_sitevar() -> None:
    with patch("logging.warning") as mock_warning:
        GoogleAnalytics.track_event("testbed", "test", "test")
        mock_warning.assert_called_with(
            "Missing sitevar: google_analytics.id. Can't track API usage."
        )


@pytest.mark.parametrize("el,ev", itertools.product([None, "test"], [None, 123]))
def test_GoogleAnalytics_track_event(el, ev) -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "abc"

    with patch("requests.get") as mock_get:
        GoogleAnalytics.track_event(
            "testbed", "test", "test", event_label=el, event_value=ev
        )

    mock_get.assert_called()
    args, kwargs = mock_get.call_args

    assert len(args) == 1
    assert len(kwargs) == 2
    assert args[0] == "https://www.google-analytics.com/collect"
    assert kwargs["timeout"] == 10

    query_components_expected = {
        "v": 1,
        "tid": "abc",
        "cid": "6dcf939a-da96-33c4-acd1-51208db9ceaa",
        "t": "event",
        "ec": "test",
        "ea": "test",
        "cd1": "testbed",
        "ni": 1,
        "sc": "end",
    }
    if el:
        query_components_expected["el"] = el
    if ev:
        query_components_expected["ev"] = ev

    assert kwargs["params"] == query_components_expected
