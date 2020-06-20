import json

from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID


def test_default_sitevar():
    default_sitevar = GoogleAnalyticsID._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"GOOGLE_ANALYTICS_ID": ""}
    assert default_sitevar.contents == default_json


def test_google_analytics_id():
    assert GoogleAnalyticsID.google_analytics_id() == ""


def test_google_analytics_id_set():
    test_id = "abc"
    Sitevar.get_or_insert(
        "google_analytics.id", values_json=json.dumps({"GOOGLE_ANALYTICS_ID": test_id})
    )
    assert GoogleAnalyticsID.google_analytics_id() == test_id
