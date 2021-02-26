import json

from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.flask_secrets import FlaskSecrets


def test_default_sitevar():
    default_sitevar = FlaskSecrets._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"secret_key": FlaskSecrets.DEFAULT_SECRET_KEY}
    assert default_sitevar.contents == default_json


def test_secret_key():
    assert FlaskSecrets.secret_key() == FlaskSecrets.DEFAULT_SECRET_KEY


def test_secrets_set():
    secret_key = "abc"
    Sitevar.get_or_insert(
        "flask.secrets", values_json=json.dumps({"secret_key": secret_key})
    )
    assert FlaskSecrets.secret_key() == secret_key
