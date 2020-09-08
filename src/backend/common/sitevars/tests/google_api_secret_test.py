import json

from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.google_api_secret import GoogleApiSecret


def test_default_sitevar():
    default_sitevar = GoogleApiSecret._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"api_key": ""}
    assert default_sitevar.contents == default_json


def test_secret_key():
    assert GoogleApiSecret.secret_key() == ""


def test_secrets_set():
    secret_key = "abc"
    Sitevar.get_or_insert(
        "google.secrets", values_json=json.dumps({"api_key": secret_key})
    )
    assert GoogleApiSecret.secret_key() == secret_key
