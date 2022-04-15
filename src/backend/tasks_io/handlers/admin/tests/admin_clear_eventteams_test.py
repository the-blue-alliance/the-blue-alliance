from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


def test_invalid_key(tasks_client: Client, login_gae_admin) -> None:
    resp = tasks_client.get("/tasks/admin/do/clear_eventteams/asdf")
    assert resp.status_code == 400


def test_missing_event(tasks_client: Client, login_gae_admin) -> None:
    resp = tasks_client.get("/tasks/admin/do/clear_eventteams/2020event")
    assert resp.status_code == 404


def test_clear_eventteams(tasks_client: Client, login_gae_admin) -> None:
    event = Event(
        id="2020event",
        year=2020,
        event_short="event",
        event_type_enum=EventType.OFFSEASON,
    )
    event.put()
    [
        EventTeam(
            id=f"2020event_frc{i}",
            event=event.key,
            team=ndb.Key(Team, f"frc{i}"),
            year=2020,
        ).put()
        for i in range(1, 11)
    ]
    assert EventTeam.query(EventTeam.event == event.key).count() == 10

    resp = tasks_client.get("/tasks/admin/do/clear_eventteams/2020event")
    assert resp.status_code == 200

    assert EventTeam.query(EventTeam.event == event.key).count() == 0
