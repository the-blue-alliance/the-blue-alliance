import importlib
import os

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask

from backend.common.sitevars.secrets import Secrets


@pytest.fixture(autouse=True)
def setup_secret_key(monkeypatch: MonkeyPatch) -> None:
    def mock_get_secret():
        return "thebluealliance-test"

    monkeypatch.setattr(Secrets, "secret_key", mock_get_secret)


def test_blueprint_not_installed_by_default() -> None:
    assert os.environ.get("GAE_ENV") is None

    from backend.web import main

    importlib.reload(main)

    client = main.app.test_client()
    resp = client.get("/local/bootstrap")
    assert resp.status_code == 404


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
