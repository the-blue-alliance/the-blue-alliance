import pytest

from backend.common.sitevars.fms_api_secrets import ContentType, FMSApiSecrets


def test_key():
    assert FMSApiSecrets.key() == "fmsapi.secrets"


def test_description():
    assert FMSApiSecrets.description() == "For accessing the FMS API"


def test_default_sitevar():
    default_sitevar = FMSApiSecrets._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"username": "", "authkey": ""}
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "For accessing the FMS API"


def test_username_default():
    assert FMSApiSecrets.username() is None


def test_authkey_default():
    assert FMSApiSecrets.authkey() is None


@pytest.mark.parametrize(
    "username, authkey, expected_username, expected_authkey",
    [
        ("", "", None, None),
        ("zach", "", "zach", None),
        ("", "authkey", None, "authkey"),
        ("zach", "authkey", "zach", "authkey"),
    ],
)
def test_username_authkey(username, authkey, expected_username, expected_authkey):
    FMSApiSecrets.put(ContentType(username=username, authkey=authkey))
    assert FMSApiSecrets.username() == expected_username
    assert FMSApiSecrets.authkey() == expected_authkey


@pytest.mark.parametrize(
    "username, authkey, auth_token",
    [
        ("", "", None),
        ("zach", "", None),
        ("", "authkey", None),
        ("zach", "authkey", "emFjaDphdXRoa2V5"),
    ],
)
def test_auth_token(username, authkey, auth_token):
    FMSApiSecrets.put(ContentType(username=username, authkey=authkey))
    assert FMSApiSecrets.auth_token() == auth_token


def test_generate_auth_token():
    auth_token = FMSApiSecrets.generate_auth_token("zach", "authkey")
    assert auth_token == "emFjaDphdXRoa2V5"
