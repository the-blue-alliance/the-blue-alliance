from typing import Any, Dict, Generator, List, Tuple
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from bs4 import BeautifulSoup
from flask import template_rendered
from flask.testing import FlaskClient
from google.appengine.ext import ndb
from jinja2 import Template

from backend.common import auth
from backend.common.models.account import Account
from backend.common.models.user import User


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    # prevent global state from leaking
    ndb.get_context().clear_cache()


@pytest.fixture
def web_client(gae_testbed) -> FlaskClient:
    from backend.web.main import app

    # Disable CSRF protection for unit testing
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False

    return app.test_client()


@pytest.fixture
def login_user(ndb_stub, monkeypatch: MonkeyPatch):
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


def get_inputs_from_form(soup: BeautifulSoup) -> Dict:
    fields = {}
    for input in soup.findAll("input"):
        # ignore submit/image with no name attribute
        if input["type"] in ["submit", "image"] and "name" not in input:
            continue

        # single element nome/value fields
        if input["type"] in ["text", "hidden", "password", "submit", "image"]:
            value = ""
            if input.has_attr("value"):
                value = input["value"]
            fields[input["name"]] = value
            continue

        # checkboxes and radios
        if input["type"] in ("checkbox", "radio"):
            value = ""
            if input.has_attr("checked"):
                if input.has_attr("value"):
                    value = input["value"]
                else:
                    value = "on"
            if input.has_attr("name") and value:
                fields[input["name"]] = value

            if not input.has_attr("name"):
                fields[input["name"]] = value

            continue

        assert False, "input type %s not supported" % input["type"]

    # textareas
    for textarea in soup.findAll("textarea"):
        fields[textarea["name"]] = textarea.string or ""

    # select fields
    for select in soup.findAll("select"):
        value = ""
        options = select.findAll("option")
        is_multiple = select.has_attr("multiple")
        selected_options = [option for option in options if option.has_attr("selected")]

        # If no select options, go with the first one
        if not selected_options and options:
            selected_options = [options[0]]

        if not is_multiple:
            assert len(selected_options) < 2
            if len(selected_options) == 1:
                value = selected_options[0]["value"]
        else:
            value = [option["value"] for option in selected_options]

        fields[select["name"]] = value

    return fields
