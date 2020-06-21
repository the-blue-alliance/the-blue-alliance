import importlib
import os

from _pytest.monkeypatch import MonkeyPatch


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
