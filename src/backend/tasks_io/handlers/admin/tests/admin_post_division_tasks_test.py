from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


def test_unauthenticated(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/admin/do/post_division_tasks/2020event")
    assert resp.status_code == 401


def test_taskqueue_header_bypasses_auth(tasks_client: Client) -> None:
    resp = tasks_client.get(
        "/tasks/admin/do/post_division_tasks/2020event",
        headers={"X-AppEngine-QueueName": "admin"},
    )
    # Not 401 - task queue requests are allowed through (404 because event doesn't exist)
    assert resp.status_code == 404


def test_invalid_key(tasks_client: Client, login_gae_admin) -> None:
    resp = tasks_client.get("/tasks/admin/do/post_division_tasks/asdf")
    assert resp.status_code == 400


def test_missing_event(tasks_client: Client, login_gae_admin) -> None:
    resp = tasks_client.get("/tasks/admin/do/post_division_tasks/2020event")
    assert resp.status_code == 404


def test_post_division_tasks(
    tasks_client: Client,
    login_gae_admin,
    taskqueue_stub,
) -> None:
    event = Event(
        id="2020cmptx",
        year=2020,
        event_short="cmptx",
        event_type_enum=EventType.CMP_FINALS,
    )
    event.put()
    [
        EventTeam(
            id=f"2020cmptx_frc{i}",
            event=event.key,
            team=ndb.Key(Team, f"frc{i}"),
            year=2020,
        ).put()
        for i in range(1, 6)
    ]
    assert EventTeam.query(EventTeam.event == event.key).count() == 5

    resp = tasks_client.get("/tasks/admin/do/post_division_tasks/2020cmptx")
    assert resp.status_code == 200

    # Event teams should be deleted
    assert EventTeam.query(EventTeam.event == event.key).count() == 0

    # Event cmp hacks should be updated
    updated_event = Event.get_by_id("2020cmptx")
    sync_overrides = none_throws(updated_event).sync_overrides or {}
    assert "event_sync_disable" not in sync_overrides
    assert sync_overrides["set_start_day_to_last"] is True
    assert sync_overrides["skip_eventteams"] is True

    # event_details task should be enqueued
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert any("/backend-tasks/get/event_details/2020cmptx" in t.url for t in tasks)


def test_post_division_tasks_idempotent_event_config(
    tasks_client: Client,
    login_gae_admin,
    taskqueue_stub,
) -> None:
    event = Event(
        id="2020cmptx",
        year=2020,
        event_short="cmptx",
        event_type_enum=EventType.CMP_FINALS,
    )
    event.put()

    event.sync_overrides = {
        "event_sync_disable": True,
        "set_start_day_to_last": True,
    }
    event.put()

    resp = tasks_client.get("/tasks/admin/do/post_division_tasks/2020cmptx")
    assert resp.status_code == 200

    updated_event = Event.get_by_id("2020cmptx")
    sync_overrides = none_throws(updated_event).sync_overrides or {}
    assert sync_overrides["event_sync_disable"] is True
    assert sync_overrides["set_start_day_to_last"] is True
    assert sync_overrides["skip_eventteams"] is True

    # event_details task should be enqueued
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert any("/backend-tasks/get/event_details/2020cmptx" in t.url for t in tasks)


def test_post_division_tasks_preserves_other_config(
    tasks_client: Client,
    login_gae_admin,
    taskqueue_stub,
) -> None:
    event = Event(
        id="2020cmptx",
        year=2020,
        event_short="cmptx",
        event_type_enum=EventType.CMP_FINALS,
        sync_overrides={
            "skip_eventteams": True,
            "event_name_override": {
                "name": "Custom Name",
                "short_name": "Custom",
            },
        },
    )
    event.put()

    resp = tasks_client.get("/tasks/admin/do/post_division_tasks/2020cmptx")
    assert resp.status_code == 200

    updated_event = Event.get_by_id("2020cmptx")
    sync_overrides = none_throws(updated_event).sync_overrides or {}
    assert "event_sync_disable" not in sync_overrides
    assert sync_overrides["set_start_day_to_last"] is True
    assert sync_overrides["skip_eventteams"] is True
    assert sync_overrides["event_name_override"] == {
        "name": "Custom Name",
        "short_name": "Custom",
    }
