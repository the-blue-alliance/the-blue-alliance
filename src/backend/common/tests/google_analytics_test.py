import itertools
from typing import Generator
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from flask import Flask
from google.appengine.ext import ndb
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from backend.common.google_analytics import GoogleAnalytics
from backend.common.run_after_response import execute_callbacks, response_context


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture(autouse=True)
def run_with_werkzeug_context(app: Flask) -> Generator:
    with app.test_request_context("/"):
        yield


def test_GoogleAnalytics_track_event_missing_sitevar() -> None:
    with patch("logging.warning") as mock_warning:
        GoogleAnalytics.track_event("testbed", "test", "test")
        mock_warning.assert_called_with(
            "Missing sitevar: google_analytics.id. Can't track API usage."
        )


@pytest.mark.parametrize(
    "run_after,el,ev", itertools.product([False, True], [None, "test"], [None, 123])
)
def test_GoogleAnalytics_track_event(run_after, el, ev) -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "abc"

    # Ensure response_context has a request object so run_after callbacks can be queued
    response_context.request = Request(create_environ(path="/"))

    # Patch the current NDB context's urlfetch to capture calls
    with patch.object(ndb.get_context(), "urlfetch") as mock_fetch:
        GoogleAnalytics.track_event(
            "testbed",
            "test",
            "test",
            event_label=el,
            event_value=ev,
            run_after=run_after,
        )
        if run_after:
            mock_fetch.assert_not_called()
        execute_callbacks()

    mock_fetch.assert_called()
    args, kwargs = mock_fetch.call_args

    assert len(args) == 1
    assert args[0].startswith("https://www.google-analytics.com/collect")
    assert kwargs["method"] == "GET"
    assert kwargs["deadline"] == 10

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

    # Compare query params in URL (all values will be strings in the URL)
    parsed = urlparse(args[0])
    query = {k: v[0] for k, v in parse_qs(parsed.query, strict_parsing=True).items()}
    # Coerce expected values to strings for comparison against URL query
    expected_as_str = {k: str(v) for k, v in query_components_expected.items()}
    assert query == expected_as_str
