from typing import Any, Dict, Generator, List, Tuple
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import template_rendered
from flask.testing import FlaskClient
from jinja2 import Template

from backend.common.models.account import Account
from backend.web import auth
from backend.web.models.user import User


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture
def web_client() -> FlaskClient:
    from backend.web.main import app

    # Disable CSRF protection for unit testing
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False

    return app.test_client()


@pytest.fixture
def login_user(ndb_client, monkeypatch: MonkeyPatch):
    with ndb_client.context():
        account = Account(
            email="test@tba.com",
            registered=True,
        )
        account_key = account.put()

    mock_user = Mock(spec=User)
    mock_user.is_registered = True
    mock_user.api_read_keys = []
    mock_user.api_write_keys = []
    mock_user.mobile_clients = []
    mock_user.permissions = []
    mock_user.account_key = account_key

    def mock_current_user():
        return mock_user

    monkeypatch.setattr(auth, "_current_user", mock_current_user)
    return mock_user


CapturedTemplate = Tuple[Template, Dict[str, Any]]  # (template, context)


@pytest.fixture
def captured_templates() -> Generator[List[CapturedTemplate], None, None]:
    from backend.web.main import app

    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)
