from backend.common.sitevars.google_analytics_id import ContentType, GoogleAnalyticsID


def test_key():
    assert GoogleAnalyticsID.key() == "google_analytics.id"


def test_description():
    assert (
        GoogleAnalyticsID.description()
        == "Google Analytics ID for logging API requests"
    )


def test_default_sitevar():
    default_sitevar = GoogleAnalyticsID._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"GOOGLE_ANALYTICS_ID": ""}
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "Google Analytics ID for logging API requests"


def test_google_analytics_id_empty():
    assert GoogleAnalyticsID.google_analytics_id() is None


def test_google_analytics_id():
    test_id = "abc"
    GoogleAnalyticsID.put(ContentType(GOOGLE_ANALYTICS_ID=test_id))
    assert GoogleAnalyticsID.google_analytics_id() == test_id
