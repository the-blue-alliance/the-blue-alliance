from unittest.mock import patch
from urllib.parse import parse_qsl, urlparse

import pytest
from google.cloud import ndb

from backend.common.google_analytics import GoogleAnalytics


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context: ndb.Context) -> None:
    pass


def test_GoogleAnalytics_track_event_missing_sitevar() -> None:
    with patch("logging.warning") as mock_warning:
        GoogleAnalytics.track_event("testbed", "test", "test")
        mock_warning.assert_called_with(
            "Missing sitevar: google_analytics.id. Can't track API usage."
        )


@pytest.mark.parametrize("ev", [(None), (123)])
def test_GoogleAnalytics_track_event(ev) -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "abc"

    with patch("urlfetch.fetch") as mock_fetch:
        GoogleAnalytics.track_event("testbed", "test", "test", ev)

    mock_fetch.assert_called()
    _, kwargs = mock_fetch.call_args

    assert len(kwargs) == 3
    assert kwargs["deadline"] == 10
    assert kwargs["method"] == "GET"

    url = kwargs["url"]
    assert url

    url_components = urlparse(url)
    assert url_components.scheme == "https"
    assert url_components.netloc == "www.google-analytics.com"
    assert url_components.path == "/collect"

    query_components = parse_qsl(url_components.query)
    assert len(query_components) == 8 + (1 if ev else 0)

    query_components_expected = {
        ("v", "1"),
        ("tid", "abc"),
        ("cid", "6dcf939a-da96-33c4-acd1-51208db9ceaa"),
        ("t", "event"),
        ("ec", "test"),
        ("ea", "test"),
        ("ni", "1"),
        ("sc", "end"),
    }
    if ev:
        query_components_expected.add(("ev", str(ev)))

    assert set(query_components) == query_components_expected
