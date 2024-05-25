from backend.common.sitevars.flask_secrets import ContentType, FlaskSecrets


def test_key():
    assert FlaskSecrets.key() == "flask.secrets"


def test_description():
    assert FlaskSecrets.description() == "Secret key for Flask session"


def test_default_sitevar():
    default_sitevar = FlaskSecrets._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {"secret_key": FlaskSecrets.DEFAULT_SECRET_KEY}
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "Secret key for Flask session"


def test_secret_key_none():
    assert FlaskSecrets.secret_key() == FlaskSecrets.DEFAULT_SECRET_KEY


def test_secret_key_empty():
    FlaskSecrets.put(ContentType(secret_key=""))
    assert FlaskSecrets.secret_key() == FlaskSecrets.DEFAULT_SECRET_KEY


def test_secrets():
    secret_key = "abc"
    FlaskSecrets.put(ContentType(secret_key=secret_key))
    assert FlaskSecrets.secret_key() == secret_key
