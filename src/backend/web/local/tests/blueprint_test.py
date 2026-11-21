import importlib
import os
from unittest.mock import Mock, mock_open, patch

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.environment import Environment
from backend.common.helpers.fms_companion_helper import FMSCompanionHelper
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
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


def test_sdk_version(local_client: Client) -> None:
    with patch(
        "backend.web.local.blueprint.open", mock_open(read_data="123.0.0"), create=True
    ):
        resp = local_client.get("/local/sdk_version")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "123.0.0"


def test_webhook_server_roundtrip(local_client: Client) -> None:
    resp = local_client.get("/local/webhooks")
    assert resp.status_code == 200
    assert resp.json == {}

    resp = local_client.post("/local/webhooks", json={"message_type": "ping"})
    assert resp.status_code == 200

    resp = local_client.get("/local/webhooks")
    assert resp.json == {"message_type": "ping"}

    # Reading the webhook clears it
    resp = local_client.get("/local/webhooks")
    assert resp.json == {}


def test_get_fms_companion_db_missing(local_client: Client) -> None:
    with patch.object(
        FMSCompanionHelper, "read_newest_companion_db", return_value=None
    ):
        resp = local_client.get("/local/get_fms_companion_db/2024test")
    assert resp.status_code == 404
    assert resp.json == {"Error": "No companion database found for event 2024test"}


def test_get_fms_companion_db(local_client: Client) -> None:
    with patch.object(
        FMSCompanionHelper, "read_newest_companion_db", return_value=b"sqlite"
    ):
        resp = local_client.get("/local/get_fms_companion_db/2024test")
    assert resp.status_code == 200
    assert resp.data == b"sqlite"
    assert resp.headers["Content-Type"] == "application/x-sqlite3"
    assert (
        resp.headers["Content-Disposition"]
        == "attachment; filename=2024test_companion.db"
    )


def test_create_test_event_invalid_key(local_client: Client) -> None:
    resp = local_client.post("/local/create_test_event/notakey")
    assert resp.status_code == 400
    assert resp.json == {"Error": "Invalid event key format."}


def test_create_test_event(local_client: Client, taskqueue_stub) -> None:
    resp = local_client.post("/local/create_test_event/2024test")
    assert resp.status_code == 200
    body = none_throws(resp.json)
    assert body["Success"] == "Event 2024test created"
    assert len(body["auth_id"]) == 16
    assert len(body["auth_secret"]) == 64

    event = none_throws(Event.get_by_id("2024test"))
    assert event.event_type_enum == EventType.OFFSEASON
    assert event.name == "2024 TEST Test Event"

    auth = none_throws(ApiAuthAccess.get_by_id(body["auth_id"]))
    assert auth.secret == body["auth_secret"]
    assert AuthType.READ_API not in auth.auth_types_enum

    # Calling again reuses the existing auth
    resp = local_client.post("/local/create_test_event/2024test")
    assert resp.status_code == 200
    assert resp.json == {
        "Success": "Event 2024test already exists",
        "event_key": "2024test",
        "auth_id": body["auth_id"],
        "auth_secret": body["auth_secret"],
    }


def test_create_test_event_existing_event_without_auth(
    local_client: Client,
) -> None:
    Event(
        id="2024test",
        year=2024,
        event_short="test",
        event_type_enum=EventType.OFFSEASON,
    ).put()
    resp = local_client.post("/local/create_test_event/2024test")
    assert resp.status_code == 200
    assert none_throws(resp.json)["Success"] == "Event 2024test created"
