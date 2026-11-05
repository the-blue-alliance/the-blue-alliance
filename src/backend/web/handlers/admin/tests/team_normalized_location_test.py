from google.appengine.api import datastore
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.helpers.deferred import run_from_task
from backend.common.models.team import Team
from backend.web.handlers.admin.team_normalized_location import (
    _purge_team_normalized_locations,
)


def _put_team(number: int, with_leftover: bool) -> None:
    Team(
        id=f"frc{number}",
        team_number=number,
        city="San Jose",
        nickname=f"Team {number}",
    ).put()
    if with_leftover:
        # Stored the way the clear task left it: only a null placeholder
        raw = datastore.Get(ndb.Key(Team, f"frc{number}").to_old_key())
        raw["normalized_location"] = None
        datastore.Put(raw)
    # Later reads see the stored entity, as a fresh task request would
    ndb.get_context().clear_cache()


def _stored(number: int) -> datastore.Entity:
    return datastore.Get(ndb.Key(Team, f"frc{number}").to_old_key())


def _has_leftover(number: int) -> bool:
    return "normalized_location" in _stored(number)


def _fresh(number: int) -> Team:
    team = Team.get_by_id(f"frc{number}", use_cache=False, use_memcache=False)
    assert team is not None
    return team


def _drain(taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub) -> int:
    count = 0
    while tasks := taskqueue_stub.get_filtered_tasks(queue_names="admin"):
        taskqueue_stub.FlushQueue("admin")
        for task in tasks:
            run_from_task(task)
            count += 1
    return count


def test_dashboard_requires_admin(web_client: Client) -> None:
    resp = web_client.get("/admin/team_normalized_location")
    assert resp.status_code == 401


def test_dashboard_requires_admin_not_user(web_client: Client, login_gae_user) -> None:
    resp = web_client.get("/admin/team_normalized_location")
    assert resp.status_code == 401


def test_purge_post_requires_admin(web_client: Client, taskqueue_stub) -> None:
    resp = web_client.post("/admin/team_normalized_location/purge")
    assert resp.status_code == 401
    assert taskqueue_stub.get_filtered_tasks(queue_names="admin") == []


def test_purge_post_requires_admin_not_user(
    web_client: Client, login_gae_user, taskqueue_stub
) -> None:
    resp = web_client.post("/admin/team_normalized_location/purge")
    assert resp.status_code == 401
    assert taskqueue_stub.get_filtered_tasks(queue_names="admin") == []


def test_dashboard_shows_remaining_count(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    _put_team(254, with_leftover=True)
    _put_team(604, with_leftover=True)
    _put_team(9999, with_leftover=False)

    resp = web_client.get("/admin/team_normalized_location")
    assert resp.status_code == 200
    assert b"<dd>2</dd>" in resp.data
    assert b"/admin/team_normalized_location/purge" in resp.data


def test_purge_post_enqueues_task(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    _put_team(254, with_leftover=True)

    resp = web_client.post("/admin/team_normalized_location/purge")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin/team_normalized_location")

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
    assert len(tasks) == 1
    run_from_task(tasks[0])

    assert not _has_leftover(254)


def test_leftover_survives_a_normal_save(ndb_stub) -> None:
    _put_team(254, with_leftover=True)

    team = _fresh(254)
    team.nickname = "Renamed"
    team.put()

    assert _has_leftover(254)


def test_purge_removes_property_and_keeps_other_fields(
    ndb_stub, taskqueue_stub
) -> None:
    _put_team(254, with_leftover=True)

    assert _purge_team_normalized_locations() == 1

    assert not _has_leftover(254)
    team = _fresh(254)
    # pyre-ignore[16]: NDB instance internals aren't in the stubs
    assert "normalized_location" not in team._properties
    assert team.city == "San Jose"
    assert team.nickname == "Team 254"


def test_purge_skips_teams_without_property(ndb_stub, taskqueue_stub) -> None:
    _put_team(254, with_leftover=True)
    _put_team(9999, with_leftover=False)
    untouched_updated = _fresh(9999).updated

    assert _purge_team_normalized_locations() == 1

    assert _fresh(9999).updated == untouched_updated


def test_purge_clears_team_caches(ndb_stub, taskqueue_stub) -> None:
    _put_team(254, with_leftover=True)

    _purge_team_normalized_locations()

    assert len(taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")) == 1


def test_purge_follows_cursor_across_batches(ndb_stub, taskqueue_stub) -> None:
    numbers = list(range(1, 8))
    for n in numbers:
        _put_team(n, with_leftover=True)

    assert _purge_team_normalized_locations(batch_size=2) == 2
    assert _drain(taskqueue_stub) == 3

    for n in numbers:
        assert not _has_leftover(n)


def test_purge_logs_running_total(ndb_stub, taskqueue_stub, caplog) -> None:
    for n in range(1, 6):
        _put_team(n, with_leftover=True)

    with caplog.at_level("INFO"):
        _purge_team_normalized_locations(batch_size=2)
        _drain(taskqueue_stub)

    assert "purge complete: 5" in caplog.text


def test_rerun_is_noop(ndb_stub, taskqueue_stub) -> None:
    for n in range(1, 4):
        _put_team(n, with_leftover=True)
    _purge_team_normalized_locations()
    updated_after_first = [_fresh(n).updated for n in range(1, 4)]

    assert _purge_team_normalized_locations() == 0

    assert [_fresh(n).updated for n in range(1, 4)] == updated_after_first
