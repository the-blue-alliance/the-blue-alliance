from backend.common.sitevars.google_api_secret import ContentType, GoogleApiSecret


def test_key():
    assert GoogleApiSecret.key() == "google.secrets"


def test_description():
    assert GoogleApiSecret.description() == "For Google API Calls"


def test_default_sitevar():
    default_sitevar = GoogleApiSecret._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"api_key": ""}
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "For Google API Calls"


def test_secret_key_empty():
    assert GoogleApiSecret.secret_key() is None


def test_secrets():
    secret_key = "abc"
    GoogleApiSecret.put(ContentType(api_key=secret_key))
    assert GoogleApiSecret.secret_key() == secret_key
