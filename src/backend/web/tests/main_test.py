import importlib

from backend.common.auth import _user_context_processor
from backend.common.environment import Environment
from backend.web.handlers.account import blueprint as account_blueprint


def test_app_secret_key(ndb_stub) -> None:
    from backend.web import main

    # Other tests might have run a request which dirties the previously
    # imported app, so let's forcibly clear it here to start clean
    importlib.reload(main)

    # Make sure the secret key is set
    assert main.app.secret_key == Environment.DEFAULT_FLASK_SECRET_KEY


def test_app_url_map_strict_slashes() -> None:
    from backend.web.main import app

    assert not app.url_map.strict_slashes


def test_app_blueprints_account() -> None:
    from backend.web.main import app

    assert app.blueprints["account"] == account_blueprint


def test_context_processor() -> None:
    from backend.web.main import app

    # The key of the dictionary is the name of the blueprint this function is active for, None for all requests
    all_processors = app.template_context_processors[None]
    assert _user_context_processor in all_processors
