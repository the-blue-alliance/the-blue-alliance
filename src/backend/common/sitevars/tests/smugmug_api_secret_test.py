from backend.common.sitevars.smugmug_api_secret import ContentType, SmugmugApiSecret


def test_key():
    assert SmugmugApiSecret.key() == "smugmug.secrets"


def test_description():
    assert SmugmugApiSecret.description() == "For SmugMug API Calls"


def test_default_sitevar():
    default_sitevar = SmugmugApiSecret._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"api_key": "", "api_secret": ""}
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "For SmugMug API Calls"


def test_api_key_empty():
    assert SmugmugApiSecret.api_key() is None


def test_secrets():
    SmugmugApiSecret.put(ContentType(api_key="abc", api_secret="def"))
    assert SmugmugApiSecret.api_key() == "abc"
    assert SmugmugApiSecret.get()["api_secret"] == "def"
