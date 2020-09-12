from typing import Any, cast, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.web.handlers.tests.conftest import CapturedTemplate


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
    assert form.find(attrs={"name": "first_code"}) is not None


def test_submit_empty_form(
    login_user,
    ndb_client: ndb.Client,
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
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_suggest_event(
    login_user,
    ndb_client: ndb.Client,
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
    with ndb_client.context():
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
        )
