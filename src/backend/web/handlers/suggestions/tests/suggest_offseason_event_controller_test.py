from typing import Any, cast, Dict, List, Optional
from unittest.mock import Mock
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.suggestions import suggestion_submission


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> Optional[Dict[str, Any]]:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_offseason_event.html"
    assert context["status"] == status

    return context.get("failures")


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/offseason")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/offseason")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="suggest_offseason")
    assert form is not None
    assert form["action"] == "/suggest/offseason"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    assert form.find(attrs={"name": "name"}) is not None
    assert form.find(attrs={"name": "start_date"}) is not None
    assert form.find(attrs={"name": "end_date"}) is not None
    assert form.find(attrs={"name": "website"}) is not None
    assert form.find(attrs={"name": "venue_name"}) is not None
    assert form.find(attrs={"name": "venue_address"}) is not None
    assert form.find(attrs={"name": "venue_city"}) is not None
    assert form.find(attrs={"name": "venue_country"}) is not None
    assert form.find(attrs={"name": "frc_events_link"}) is not None


def test_submit_empty_form(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post("/suggest/offseason", data={}, follow_redirects=True)
    assert resp.status_code == 200
    failures = assert_template_status(captured_templates, "validation_failure")
    assert failures is not None
    assert set(failures.keys()) == {
        "name",
        "start_date",
        "end_date",
        "website",
        "venue_address",
        "venue_name",
        "venue_city",
        "venue_state",
        "venue_country",
    }

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="validation_failure-alert") is not None

    # Assert no suggestions were written
    assert Suggestion.query().fetch() == []


def test_suggest_event(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    form = {}
    form["name"] = "Test Event"
    form["start_date"] = "2012-04-04"
    form["end_date"] = "2012-04-06"
    form["website"] = "http://foo.com/bar"
    form["venue_name"] = "This is a Venue"
    form["venue_address"] = "123 Fake St"
    form["venue_city"] = "New York"
    form["venue_state"] = "NY"
    form["venue_country"] = "USA"

    resp = web_client.post("/suggest/offseason", data=form, follow_redirects=True)
    assert resp.status_code == 200
    assert_template_status(captured_templates, "success")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="success-alert") is not None

    # Make sure the Suggestion gets created
    suggestion = cast(Suggestion, Suggestion.query().fetch()[0])
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
    assert suggestion.target_key is None
    assert suggestion.target_model == "offseason-event"
    assert suggestion.contents == SuggestionDict(
        name="Test Event",
        start_date="2012-04-04",
        end_date="2012-04-06",
        website="http://foo.com/bar",
        address="123 Fake St",
        city="New York",
        state="NY",
        country="USA",
        venue_name="This is a Venue",
        first_code=None,
        event_type=EventType.OFFSEASON,
    )


def test_suggest_event_with_valid_frc_events_link(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
    monkeypatch,
) -> None:
    class MockFRCResponse:
        status_code = 200

        def json(self):
            return {
                "Events": [
                    {
                        "code": "INLAF",
                        "name": "Test Event",
                        "dateStart": "2012-04-04T00:00:00",
                        "dateEnd": "2012-04-06T00:00:00",
                    }
                ]
            }

    class MockFuture:
        def get_result(self):
            return MockFRCResponse()

    class MockFRCAPI:
        def event_info(self, year: int, event_short: str):
            assert year == 2012
            assert event_short == "INLAF"
            return MockFuture()

    monkeypatch.setattr(suggestion_submission, "FRCAPI", MockFRCAPI)

    form = {
        "name": "Test Event",
        "start_date": "2012-04-04",
        "end_date": "2012-04-06",
        "website": "http://foo.com/bar",
        "venue_name": "This is a Venue",
        "venue_address": "123 Fake St",
        "venue_city": "New York",
        "venue_state": "NY",
        "venue_country": "USA",
        "frc_events_link": "https://frc-events.firstinspires.org/2012/INLAF",
    }

    resp = web_client.post("/suggest/offseason", data=form, follow_redirects=True)
    assert resp.status_code == 200
    assert_template_status(captured_templates, "success")

    suggestion = cast(Suggestion, Suggestion.query().fetch()[0])
    assert suggestion.contents["first_code"] == "INLAF"


def test_suggest_event_with_invalid_frc_events_link_format(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    form = {
        "name": "Test Event",
        "start_date": "2012-04-04",
        "end_date": "2012-04-06",
        "website": "http://foo.com/bar",
        "venue_name": "This is a Venue",
        "venue_address": "123 Fake St",
        "venue_city": "New York",
        "venue_state": "NY",
        "venue_country": "USA",
        "frc_events_link": "https://example.com/2012/INLAF",
    }

    resp = web_client.post("/suggest/offseason", data=form, follow_redirects=True)
    assert resp.status_code == 200
    failures = assert_template_status(captured_templates, "validation_failure")
    assert failures is not None
    assert "frc_events_link" in failures

    assert Suggestion.query().fetch() == []


def test_suggest_event_with_mismatched_frc_events_link(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
    monkeypatch,
) -> None:
    class MockFRCResponse:
        status_code = 200

        def json(self):
            return {
                "Events": [
                    {
                        "code": "INLAF",
                        "name": "Different Event",
                        "dateStart": "2012-04-04T00:00:00",
                        "dateEnd": "2012-04-06T00:00:00",
                    }
                ]
            }

    class MockFuture:
        def get_result(self):
            return MockFRCResponse()

    class MockFRCAPI:
        def event_info(self, year: int, event_short: str):
            assert year == 2012
            assert event_short == "INLAF"
            return MockFuture()

    monkeypatch.setattr(suggestion_submission, "FRCAPI", MockFRCAPI)

    form = {
        "name": "Test Event",
        "start_date": "2012-04-04",
        "end_date": "2012-04-06",
        "website": "http://foo.com/bar",
        "venue_name": "This is a Venue",
        "venue_address": "123 Fake St",
        "venue_city": "New York",
        "venue_state": "NY",
        "venue_country": "USA",
        "frc_events_link": "https://frc-events.firstinspires.org/2012/INLAF",
    }

    resp = web_client.post("/suggest/offseason", data=form, follow_redirects=True)
    assert resp.status_code == 200
    failures = assert_template_status(captured_templates, "validation_failure")
    assert failures is not None
    assert "frc_events_link" in failures

    assert Suggestion.query().fetch() == []


def test_suggest_event_alerts_admins(
    login_user,
    ndb_stub,
    taskqueue_stub,
    run_deferred_tasks,
    sent_admin_alerts,
    web_client: Client,
) -> None:
    resp = web_client.post(
        "/suggest/offseason",
        data={
            "name": "Test Event",
            "start_date": "2012-04-04",
            "end_date": "2012-04-06",
            "website": "http://foo.com/bar",
            "venue_name": "This is a Venue",
            "venue_address": "123 Fake St",
            "venue_city": "New York",
            "venue_state": "NY",
            "venue_country": "USA",
        },
    )
    assert resp.status_code == 302

    assert sent_admin_alerts == []
    assert run_deferred_tasks() == 1
    subject, body = sent_admin_alerts[0]
    assert subject == "New Offseason Event Suggestion: Test Event"
    assert "Test Event" in body
    assert "suggest/review/offseason-event" in body


def test_suggest_event_no_alert_on_validation_failure(
    login_user,
    ndb_stub,
    taskqueue_stub,
    run_deferred_tasks,
    sent_admin_alerts,
    web_client: Client,
) -> None:
    resp = web_client.post("/suggest/offseason", data={"name": "Missing dates"})
    assert resp.status_code == 200
    assert Suggestion.query().count() == 0
    assert run_deferred_tasks() == 0
    assert sent_admin_alerts == []


def _mock_frc_api(
    monkeypatch, status_code: int = 200, events: Optional[List[Dict[str, Any]]] = None
) -> None:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = {"Events": events} if events is not None else None
    api = Mock()
    api.return_value.event_info.return_value.get_result.return_value = response
    monkeypatch.setattr(suggestion_submission, "FRCAPI", api)


_LINK = "https://frc-events.firstinspires.org/2012/INLAF"
_EVENT = {
    "code": "INLAF",
    "name": "Test Event",
    "dateStart": "2012-04-04T00:00:00",
    "dateEnd": "2012-04-06T00:00:00",
}


def test_get_frc_event_code_bad_path() -> None:
    code, error = suggestion_submission._get_frc_event_code(
        "https://frc-events.firstinspires.org/not/a/valid/path", "", "", ""
    )
    assert code is None
    assert error is not None and error.startswith("Invalid frc-events link")


def test_get_frc_event_code_api_exception(monkeypatch) -> None:
    api = Mock()
    api.return_value.event_info.side_effect = Exception("boom")
    monkeypatch.setattr(suggestion_submission, "FRCAPI", api)
    assert suggestion_submission._get_frc_event_code(_LINK, "", "", "") == (
        None,
        "Unable to validate frc-events link right now",
    )


def test_get_frc_event_code_api_error_status(monkeypatch) -> None:
    _mock_frc_api(monkeypatch, status_code=404)
    assert suggestion_submission._get_frc_event_code(_LINK, "", "", "") == (
        None,
        "Could not find this event on the FRC API",
    )


def test_get_frc_event_code_no_matching_event(monkeypatch) -> None:
    _mock_frc_api(monkeypatch, events=None)
    assert suggestion_submission._get_frc_event_code(_LINK, "", "", "") == (
        None,
        "Could not find this event on the FRC API",
    )


def test_get_frc_event_code_start_date_mismatch(monkeypatch) -> None:
    _mock_frc_api(monkeypatch, events=[_EVENT])
    assert suggestion_submission._get_frc_event_code(
        _LINK, "Test Event", "2012-04-05", ""
    ) == (None, "frc-events link must point to the same start date")


def test_get_frc_event_code_end_date_mismatch(monkeypatch) -> None:
    _mock_frc_api(monkeypatch, events=[_EVENT])
    assert suggestion_submission._get_frc_event_code(
        _LINK, "Test Event", "2012-04-04", "2012-04-07"
    ) == (None, "frc-events link must point to the same end date")


def test_get_frc_event_code_year_mismatch(monkeypatch) -> None:
    _mock_frc_api(monkeypatch, events=[{"code": "INLAF"}])
    assert suggestion_submission._get_frc_event_code(
        _LINK, "Test Event", "2013-04-04", ""
    ) == (None, "frc-events link year must match the event year")


def test_get_frc_event_code_unparseable_start_date(monkeypatch) -> None:
    _mock_frc_api(monkeypatch, events=[{"code": "INLAF"}])
    assert suggestion_submission._get_frc_event_code(
        _LINK, "Test Event", "not-a-date", ""
    ) == ("INLAF", None)
