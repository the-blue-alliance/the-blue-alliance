from unittest.mock import patch

from flask.testing import FlaskClient
from freezegun import freeze_time
from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.team import Team


def test_seed_blocked_in_prod(web_client: FlaskClient, login_gae_admin) -> None:
    with patch(
        "backend.web.handlers.admin.dev_tools.Environment.is_dev", return_value=False
    ):
        resp = web_client.post("/admin/dev/events/seed_test_event")
    assert resp.status_code == 403


@freeze_time("2025-03-15")
def test_seed_creates_event_and_matches(
    web_client: FlaskClient, login_gae_admin, taskqueue_stub
) -> None:
    with patch(
        "backend.web.handlers.admin.dev_tools.Environment.is_dev", return_value=True
    ):
        resp = web_client.post("/admin/dev/events/seed_test_event")
    assert resp.status_code == 302
    assert "/admin/event/2025test" in resp.headers["Location"]

    # Verify event
    event = Event.get_by_id("2025test")
    assert event is not None
    assert event.name == "North Pole Regional"
    assert event.year == 2025

    # Verify matches: 15 completed + 8 scheduled + 5 unscheduled = 28
    matches = Match.query(Match.event == ndb.Key(Event, "2025test")).fetch()
    assert len(matches) == 28

    completed = [m for m in matches if m.actual_time is not None]
    assert len(completed) == 15
    for m in completed:
        assert m.alliances["red"]["score"] >= 20
        assert m.alliances["blue"]["score"] >= 20

    scheduled = [
        m for m in matches if m.actual_time is None and m.time is not None
    ]
    assert len(scheduled) == 8
    for m in scheduled:
        assert m.alliances["red"]["score"] == -1
        assert m.alliances["blue"]["score"] == -1

    unscheduled = [
        m for m in matches if m.actual_time is None and m.time is None
    ]
    assert len(unscheduled) == 5
    for m in unscheduled:
        assert m.alliances["red"]["score"] == -1

    # Verify EventTeam records
    event_teams = EventTeam.query(
        EventTeam.event == ndb.Key(Event, "2025test")
    ).fetch()
    assert len(event_teams) == 21


@freeze_time("2025-03-15")
def test_seed_with_existing_teams(
    web_client: FlaskClient, login_gae_admin, taskqueue_stub
) -> None:
    # Pre-create some teams
    for i in range(1, 10):
        Team(id=f"frc{i}", team_number=i, nickname=f"Team {i}").put()

    with patch(
        "backend.web.handlers.admin.dev_tools.Environment.is_dev", return_value=True
    ):
        resp = web_client.post("/admin/dev/events/seed_test_event")
    assert resp.status_code == 302

    # Verify matches were created using existing teams
    matches = Match.query(Match.event == ndb.Key(Event, "2025test")).fetch()
    assert len(matches) == 28

    # All team keys should reference teams from the pre-created set
    all_team_keys = set()
    for m in matches:
        all_team_keys.update(m.team_key_names)
    for tk in all_team_keys:
        team = Team.get_by_id(tk)
        assert team is not None


@freeze_time("2025-03-15")
def test_seed_idempotent(
    web_client: FlaskClient, login_gae_admin, taskqueue_stub
) -> None:
    with patch(
        "backend.web.handlers.admin.dev_tools.Environment.is_dev", return_value=True
    ):
        resp1 = web_client.post("/admin/dev/events/seed_test_event")
        resp2 = web_client.post("/admin/dev/events/seed_test_event")

    assert resp1.status_code == 302
    assert resp2.status_code == 302

    # Should still have exactly 28 matches (createOrUpdate is idempotent)
    matches = Match.query(Match.event == ndb.Key(Event, "2025test")).fetch()
    assert len(matches) == 28
