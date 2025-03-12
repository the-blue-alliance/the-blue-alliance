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
    app.secret_key = "testsecret"

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
    mock_user.is_admin = False
    mock_user.api_read_keys = []
    mock_user.api_write_keys = []
    mock_user.mobile_clients = []
    mock_user.permissions = []
    mock_user.account_key = account_key
    mock_user.uid = account_key.id()

    def mock_current_user():
        return mock_user

    monkeypatch.setattr(auth, "_current_user", mock_current_user)
    return mock_user


@pytest.fixture
def login_admin(login_user):
    login_user.is_admin = True
    return login_user


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
    for form_input in soup.find_all("input"):
        # ignore submit/image with no name attribute
        if form_input["type"] in ["submit", "image"] and "name" not in form_input:
            continue

        # single element nome/value fields
        if form_input["type"] in ["text", "hidden", "password", "submit", "image"]:
            value = ""
            if form_input.has_attr("value"):
                value = form_input["value"]
            fields[form_input["name"]] = value
            continue

        # checkboxes and radios
        if form_input["type"] in ("checkbox", "radio"):
            value = ""
            if form_input.has_attr("checked"):
                if form_input.has_attr("value"):
                    value = form_input["value"]
                else:
                    value = "on"
            if form_input.has_attr("name") and value:
                fields[form_input["name"]] = value

            if not form_input.has_attr("name"):
                fields[form_input["name"]] = value

            continue

        assert False, "input type %s not supported" % form_input["type"]

    # textareas
    for textarea in soup.find_all("textarea"):
        fields[textarea["name"]] = textarea.string or ""

    # select fields
    for select in soup.find_all("select"):
        value = ""
        options = select.find_all("option")
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


@pytest.fixture
def setup_full_team(test_data_importer) -> None:
    test_data_importer.import_team(__file__, "tests/data/frc148.json")
    test_data_importer.import_event_list(
        __file__, "tests/data/frc148_events_2019.json", "frc148"
    )
    test_data_importer.import_match_list(
        __file__, "tests/data/frc148_matches_2019.json"
    )
    test_data_importer.import_media_list(
        __file__, "tests/data/frc148_media_2019.json", 2019, "frc148"
    )
    test_data_importer.import_media_list(
        __file__, "tests/data/frc148_social_media.json", team_key="frc148"
    )
    test_data_importer.import_award_list(__file__, "tests/data/frc148_awards_2019.json")
    test_data_importer.import_district_list(
        __file__, "tests/data/frc148_districts.json", "frc148"
    )
    test_data_importer.import_robot_list(__file__, "tests/data/frc148_robots.json")


@pytest.fixture
def setup_full_event(test_data_importer):
    # So we can import different event keys, return a function

    def import_event(event_key) -> None:
        test_data_importer.import_event(__file__, f"tests/data/{event_key}.json")
        test_data_importer.import_match_list(
            __file__, f"tests/data/{event_key}_matches.json"
        )
        test_data_importer.import_event_alliances(
            __file__, f"tests/data/{event_key}_alliances.json", event_key
        )
        test_data_importer.import_event_teams(
            __file__, f"tests/data/{event_key}_teams.json", event_key
        )

    return import_event


@pytest.fixture
def setup_event_preductions(test_data_importer):
    # So we can import different event keys, return a function

    def import_event(event_key) -> None:
        test_data_importer.import_event_predictions(
            __file__, f"tests/data/{event_key}_predictions.json", event_key
        )

    return import_event


@pytest.fixture
def setup_full_match(test_data_importer):
    def import_match(match_key) -> None:
        event_key = match_key.split("_")[0]
        test_data_importer.import_event(__file__, f"tests/data/{event_key}.json")
        test_data_importer.import_match(__file__, f"tests/data/{match_key}.json")

    return import_match


@pytest.fixture
def setup_full_year_events(test_data_importer) -> None:
    test_data_importer.import_event_list(__file__, "tests/data/all_events_2019.json")


@pytest.fixture
def setup_hof_awards(test_data_importer) -> None:
    def import_event(event_key, team_keys) -> None:
        for team_key in team_keys:
            test_data_importer.import_team(__file__, f"tests/data/{team_key}.json")

        test_data_importer.import_event(__file__, f"tests/data/{event_key}.json")
        test_data_importer.import_award_list(
            __file__, f"tests/data/{event_key}_awards.json"
        )

    return import_event
