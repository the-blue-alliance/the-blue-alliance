import importlib

import pytest
from _pytest.monkeypatch import MonkeyPatch
from werkzeug.test import Client


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture()
def mock_dev_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")


@pytest.fixture
def local_client(mock_dev_env) -> Client:
    # Since this depends on an env var, we may end up
    # with a cached version of the module, so reload
    # it after we've set up the env variables
    from backend.web import main

    importlib.reload(main)

    # Disable CSRF protection for unit testing
    main.app.config["WTF_CSRF_CHECK_DEFAULT"] = False

    return main.app.test_client()
