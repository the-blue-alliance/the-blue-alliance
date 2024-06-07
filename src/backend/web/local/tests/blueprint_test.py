import importlib
import os
from unittest.mock import Mock, patch

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask

from backend.common.environment import Environment
from backend.web.local.blueprint import local_routes, maybe_register


@pytest.fixture(autouse=True)
def setup_secret_key(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(Environment, "flask_secret_key", lambda: "thebluealliance-test")


def test_blueprint_not_installed_by_default() -> None:
    assert os.environ.get("GAE_ENV") is None

    from backend.web import main

    importlib.reload(main)

    client = main.app.test_client()
    resp = client.get("/local/bootstrap")
    assert resp.status_code == 404


def test_install_defer_routes_not_installed_in_prod(monkeypatch: MonkeyPatch) -> None:
    assert os.environ.get("GAE_ENV") is None

    app = Flask(__name__)

    with patch(
        "backend.common.deferred.install_defer_routes"
    ) as mock_install_defer_routes:
        maybe_register(app, Mock())

    mock_install_defer_routes.assert_not_called()


def test_install_defer_routes(mock_dev_env) -> None:
    assert os.environ.get("GAE_ENV") == "localdev"

    app = Flask(__name__)

    with patch(
        "backend.common.deferred.install_defer_routes"
    ) as mock_install_defer_routes:
        maybe_register(app, Mock())

    mock_install_defer_routes.assert_called()


def test_blueprint_not_installed_on_prod(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")
    assert os.environ.get("GAE_ENV") == "standard"

    from backend.web import main

    importlib.reload(main)

    client = main.app.test_client()
    resp = client.get("/local/bootstrap")
    assert resp.status_code == 404


def test_blueprint_installed_when_local_env(mock_dev_env) -> None:
    assert os.environ.get("GAE_ENV") == "localdev"

    from backend.web import main

    importlib.reload(main)

    client = main.app.test_client()
    resp = client.get("/local/bootstrap")
    assert resp.status_code == 200


def test_fail_if_mistakenly_installed_on_prod() -> None:
    from backend.web.local.blueprint import local_routes

    assert os.environ.get("GAE_ENV") is None
    app = Flask(__name__)
    app.register_blueprint(local_routes)

    client = app.test_client()
    resp = client.get("/local/bootstrap")
    assert resp.status_code == 403


def test_csrf_prod(monkeypatch: MonkeyPatch) -> None:
    assert os.environ.get("GAE_ENV") is None

    app = Flask(__name__)

    mock_csrf = Mock()
    maybe_register(app, mock_csrf)

    mock_csrf.exempt.assert_not_called()


def test_csrf_local(mock_dev_env) -> None:
    assert os.environ.get("GAE_ENV") == "localdev"

    app = Flask(__name__)

    mock_csrf = Mock()
    maybe_register(app, mock_csrf)

    mock_csrf.exempt.assert_called_with(local_routes)
