import json

from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.secrets import Secrets


def test_default_sitevar():
    default_sitevar = Secrets._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"secret_key": Secrets.DEFAULT_SECRET_KEY}
    assert default_sitevar.contents == default_json


def test_secret_key():
    assert Secrets.secret_key() == Secrets.DEFAULT_SECRET_KEY


def test_secrets_set():
    secret_key = "abc"
    Sitevar.get_or_insert("secrets", values_json=json.dumps({"secret_key": secret_key}))
    assert Secrets.secret_key() == secret_key
