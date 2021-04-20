import json

import pytest

from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.fmsapi_secrets import FMSAPISecrets


def test_key():
    assert FMSAPISecrets.key() == "fmsapi.secrets"


def test_default_sitevar():
    default_sitevar = FMSAPISecrets._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"username": "", "authkey": ""}
    assert default_sitevar.contents == default_json


def test_username_default():
    assert FMSAPISecrets.username() is None


def test_username():
    username = "zach"
    Sitevar.get_or_insert(
        FMSAPISecrets.key(), values_json=json.dumps({"username": username})
    )
    assert FMSAPISecrets.username() == username


def test_authkey_default():
    assert FMSAPISecrets.authkey() is None


def test_authkey():
    authkey = "authkey"
    Sitevar.get_or_insert(
        FMSAPISecrets.key(), values_json=json.dumps({"authkey": authkey})
    )
    assert FMSAPISecrets.authkey() == authkey


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
    Sitevar.get_or_insert(
        FMSAPISecrets.key(),
        values_json=json.dumps({"username": username, "authkey": authkey}),
    )
    assert FMSAPISecrets.auth_token() == auth_token
