from backend.common.sitevars.apiv3_key import Apiv3Key, ContentType


def test_key():
    assert Apiv3Key.key() == "apiv3_key"


def test_description():
    assert Apiv3Key.description() == "APIv3 key"


def test_default_sitevar():
    default_sitevar = Apiv3Key._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"apiv3_key": ""}
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "APIv3 key"


def test_apiv3_key_none():
    assert Apiv3Key.api_key() is None


def test_apiv3_key_empty():
    Apiv3Key.put(ContentType(apiv3_key=""))
    assert Apiv3Key.api_key() is None


def test_apiv3_key():
    key = "abcd"
    Apiv3Key.put(ContentType(apiv3_key=key))
    assert Apiv3Key.api_key() == key
