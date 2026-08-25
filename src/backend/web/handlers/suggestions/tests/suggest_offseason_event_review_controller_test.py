import datetime
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.handlers.conftest import get_inputs_from_form


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_OFFSEASON_EVENTS]
    return login_user


def get_suggestion_queue_and_fields(
    web_client: Client, form_id: Optional[str] = None
) -> Tuple[List[str], Dict]:
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_offseasons")
    assert review_form is not None
    suggestions = review_form.find_all(id=re.compile("review_.*"))
    queue = []
    for suggestion in suggestions:
        queue.append(int(suggestion["id"].split("review_")[1]))

    inputs = None
    if form_id:
        form = soup.find(id=form_id)
        assert form is not None
        inputs = get_inputs_from_form(form)

    return queue, (inputs or {})


def createSuggestion(
    logged_in_user,
    name: str = "Test Event",
    city: str = "New York",
    state: str = "NY",
) -> int:
    status = SuggestionCreator.createOffseasonEventSuggestion(
        logged_in_user.account_key,
        name,
        "2016-10-12",
        "2016-10-13",
        "http://foo.bar.com",
        "Venue Name",
        "123 Fake St",
        city,
        state,
        "USA",
    )
    assert status[0] == SuggestionCreationStatus.SUCCESS
    return none_throws(Suggestion.query().fetch(keys_only=True)[0].integer_id())


def createEvent(
    event_key: str,
    name: str,
    city: str = "New York",
    state: str = "NY",
    event_type: EventType = EventType.OFFSEASON,
) -> Event:
    year = int(event_key[:4])
    event = Event(
        id=event_key,
        event_short=event_key[4:],
        year=year,
        name=name,
        event_type_enum=event_type,
        city=city,
        state_prov=state,
        country="USA",
        start_date=datetime.datetime(year, 10, 12),
        end_date=datetime.datetime(year, 10, 13),
    )
    event.put()
    return event


def get_similar_events(web_client: Client) -> Dict[str, List[str]]:
    """
    Returns the event keys the review page suggests as prior instances of each
    pending suggestion, keyed by the heading they are listed under.
    """
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_offseasons")
    assert review_form is not None

    similar_events = {}
    for heading in review_form.find_all("h3", string=re.compile("^Similar Events")):
        similar_events[heading.get_text(strip=True)] = [
            link["href"].split("/event/")[1]
            for link in heading.find_next_sibling("ul").find_all("a")
        ]
    return similar_events


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue, _ = get_suggestion_queue_and_fields(web_client)
    assert queue == []


def test_accept_suggestion(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "test"
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    event = Event.get_by_id("2016test")
    assert event is not None


def test_accept_suggestion_normalize_event_short_and_first_code(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "TEST"
    form_fields["first_code"] = "frctest"
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    event = Event.get_by_id("2016test")
    assert event is not None
    assert event.event_short == "test"
    assert event.official is True
    assert event.first_code == "FRCTEST"


def test_accept_suggestion_strips_first_code_whitespace(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "test"
    form_fields["first_code"] = " frctest "
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    event = Event.get_by_id("2016test")
    assert event is not None
    assert event.first_code == "FRCTEST"
    assert event.official is True


def test_reject_suggestion(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "test"
    form_fields["verdict"] = "reject"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED

    event = Event.get_by_id("2016test")
    assert event is None


def createPreseasonSuggestion(logged_in_user) -> int:
    """Create a suggestion with a January date (should be PRESEASON)"""
    status = SuggestionCreator.createOffseasonEventSuggestion(
        logged_in_user.account_key,
        "Preseason Event",
        "2016-02-12",
        "2016-02-13",
        "http://foo.bar.com",
        "Venue Name",
        "123 Fake St",
        "New York",
        "NY",
        "USA",
    )
    assert status[0] == SuggestionCreationStatus.SUCCESS
    return none_throws(Suggestion.query().fetch(keys_only=True)[0].integer_id())


def test_accept_suggestion_preseason(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    """Verify that accepting a preseason suggestion creates a PRESEASON event"""
    suggestion_id = createPreseasonSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "pretest"
    form_fields["event_type_enum"] = str(EventType.PRESEASON)
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    event = Event.get_by_id("2016pretest")
    assert event is not None
    assert event.event_type_enum == EventType.PRESEASON


def test_accept_suggestion_default_offseason(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    """Verify that accepting without specifying event_type defaults to OFFSEASON"""
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "test"
    form_fields["verdict"] = "accept"
    # Remove event_type_enum to test default behavior
    form_fields.pop("event_type_enum", None)
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    event = Event.get_by_id("2016test")
    assert event is not None
    assert event.event_type_enum == EventType.OFFSEASON


def test_accept_suggestion_override_to_offseason(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    """Verify that admin can override a preseason suggestion to offseason"""
    suggestion_id = createPreseasonSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields != {}

    form_fields["event_short"] = "overtest"
    form_fields["event_type_enum"] = str(EventType.OFFSEASON)
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    event = Event.get_by_id("2016overtest")
    assert event is not None
    assert event.event_type_enum == EventType.OFFSEASON


def test_accept_creates_audit_log_with_new_event_key(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]

    form_fields["event_short"] = "test"
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
    )
    assert response.status_code == 302

    entries = AuditLogEntry.query().fetch()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.account == login_user_with_permission.account_key
    assert entry.endpoint == "suggestion_review.suggest_offseason_review"
    assert entry.target_key == ndb.Key("Event", "2016test")


def test_reject_does_not_create_audit_log(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
) -> None:
    """Rejected offseason suggestions have no event key, so no audit log is written."""
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]

    form_fields["verdict"] = "reject"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
    )
    assert response.status_code == 302

    assert AuditLogEntry.query().count() == 0


def test_similar_event_from_last_year_is_surfaced_despite_rename(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    """Offseason events get renamed year to year, often to or from an acronym"""
    createSuggestion(
        login_user_with_permission,
        name="South Carolina Robotics Invitational & Workshops",
        city="Columbia",
        state="SC",
    )
    createEvent("2015scriw", "SCRIW XII", city="Columbia", state="SC")

    assert get_similar_events(web_client)["Similar Events in 2015"] == ["2015scriw"]


def test_similar_preseason_event_is_surfaced(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    """Prior instances of an event may have been categorized as preseason"""
    createSuggestion(login_user_with_permission, name="Blue Twilight Week Zero")
    createEvent(
        "2015mnbt",
        "Blue Twilight Week Zero Invitational",
        event_type=EventType.PRESEASON,
    )

    assert get_similar_events(web_client)["Similar Events in 2015"] == ["2015mnbt"]


def test_similar_event_from_the_suggested_year_is_surfaced(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    """The event short of a recurring event changes year to year, so an event
    that already exists this year won't be caught by the duplicate key check"""
    createSuggestion(login_user_with_permission, name="Texas Robotics Invitational")
    createEvent("2016txhou1", "Texas Robotics Invitational")

    assert get_similar_events(web_client)["Similar Events in 2016"] == ["2016txhou1"]


def test_unrelated_event_is_not_surfaced(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    """Nearly every FRC event name shares words with every other one"""
    createSuggestion(
        login_user_with_permission,
        name="Where is Wolcott Invitational",
        city="Wolcott",
        state="CT",
    )
    createEvent("2015txri", "Texas Robotics Invitational", city="Houston", state="TX")

    assert get_similar_events(web_client)["Similar Events in 2015"] == []


def test_official_events_are_not_surfaced(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    createSuggestion(login_user_with_permission, name="Rocket City Regional")
    createEvent("2015alhu", "Rocket City Regional", event_type=EventType.REGIONAL)

    assert get_similar_events(web_client)["Similar Events in 2015"] == []


@freeze_time("2020-06-01")
def test_similar_events_are_compared_against_the_suggested_year(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    """Suggestions are reviewed whenever a reviewer gets to them, which may be
    a different year than the one the suggested event happens in"""
    createSuggestion(login_user_with_permission, name="Beach Blitz")
    createEvent("2015cabl", "Beach Blitz")
    createEvent("2019cabl", "Beach Blitz")

    similar_events = get_similar_events(web_client)
    assert similar_events["Similar Events in 2015"] == ["2015cabl"]
    assert "Similar Events in 2019" not in similar_events
