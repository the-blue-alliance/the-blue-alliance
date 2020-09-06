from typing import Any, Dict, Generator, List, Tuple
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import template_rendered
from flask.testing import FlaskClient
from jinja2 import Template

from backend.common.models.account import Account
from backend.web import auth


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

    mock_user = Mock()
    mock_user.is_registered = True
    mock_user.api_read_keys = []
    mock_user.api_write_keys = []
    mock_user.mobile_clients = []
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


@pytest.fixture
def setup_full_team(test_data_importer) -> None:
    test_data_importer.import_team(__file__, "data/frc148.json")
    test_data_importer.import_event_list(
        __file__, "data/frc148_events_2019.json", "frc148"
    )
    test_data_importer.import_match_list(__file__, "data/frc148_matches_2019.json")
    test_data_importer.import_media_list(
        __file__, "data/frc148_media_2019.json", 2019, "frc148"
    )
    test_data_importer.import_media_list(
        __file__, "data/frc148_social_media.json", team_key="frc148"
    )
    test_data_importer.import_award_list(__file__, "data/frc148_awards_2019.json")
    test_data_importer.import_district_list(
        __file__, "data/frc148_districts.json", "frc148"
    )
    test_data_importer.import_robot_list(__file__, "data/frc148_robots.json")


@pytest.fixture
def setup_full_event(test_data_importer):
    # So we can import different event keys, return a function

    def import_event(event_key) -> None:
        test_data_importer.import_event(__file__, f"data/{event_key}.json")
        test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
        test_data_importer.import_event_alliances(
            __file__, f"data/{event_key}_alliances.json", event_key
        )

    return import_event


@pytest.fixture
def setup_full_match(test_data_importer):
    def import_match(match_key) -> None:
        event_key = match_key.split("_")[0]
        test_data_importer.import_event(__file__, f"data/{event_key}.json")
        test_data_importer.import_match(__file__, f"data/{match_key}.json")

    return import_match


@pytest.fixture
def setup_full_year_events(test_data_importer) -> None:
    test_data_importer.import_event_list(__file__, "data/all_events_2019.json")
