from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.helpers.deferred import run_from_task
from backend.common.models.location import Location
from backend.common.models.team import Team
from backend.web.handlers.admin.team_normalized_location import (
    _clear_team_normalized_locations,
)


def _put_team(number: int, with_location: bool) -> Team:
    team = Team(
        id=f"frc{number}",
        team_number=number,
        city="San Jose",
        nickname=f"Team {number}",
        normalized_location=(
            Location(country="USA", place_details={"name": f"Team {number} HQ"})
            if with_location
            else None
        ),
    )
    team.put()
    return team


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


def test_clear_post_requires_admin(web_client: Client, taskqueue_stub) -> None:
    resp = web_client.post("/admin/team_normalized_location/clear")
    assert resp.status_code == 401
    assert taskqueue_stub.get_filtered_tasks(queue_names="admin") == []


def test_dashboard_shows_remaining_count(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    _put_team(254, with_location=True)
    _put_team(604, with_location=True)
    _put_team(9999, with_location=False)

    resp = web_client.get("/admin/team_normalized_location")
    assert resp.status_code == 200
    assert b"<dd>2</dd>" in resp.data
    assert b"/admin/team_normalized_location/clear" in resp.data


def test_clear_post_enqueues_task(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    _put_team(254, with_location=True)

    resp = web_client.post("/admin/team_normalized_location/clear")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin/team_normalized_location")

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
    assert len(tasks) == 1
    run_from_task(tasks[0])

    assert _fresh(254).normalized_location is None


def test_clear_only_touches_teams_with_location(ndb_stub, taskqueue_stub) -> None:
    _put_team(254, with_location=True)
    untouched = _put_team(9999, with_location=False)

    totals = _clear_team_normalized_locations()

    assert totals == {"scanned": 2, "cleared": 1}
    cleared = _fresh(254)
    assert cleared.normalized_location is None
    assert cleared.city == "San Jose"
    assert cleared.nickname == "Team 254"
    # Not rewritten
    assert _fresh(9999).updated == untouched.updated


def test_clear_follows_cursor_across_batches(ndb_stub, taskqueue_stub) -> None:
    numbers = list(range(1, 8))
    for n in numbers:
        _put_team(n, with_location=n % 2 == 1)

    first = _clear_team_normalized_locations(batch_size=2)
    assert first == {"scanned": 2, "cleared": 1}
    assert _drain(taskqueue_stub) == 3

    for n in numbers:
        assert _fresh(n).normalized_location is None


def test_clear_logs_running_totals(ndb_stub, taskqueue_stub, caplog) -> None:
    for n in range(1, 6):
        _put_team(n, with_location=True)

    with caplog.at_level("INFO"):
        _clear_team_normalized_locations(batch_size=2)
        _drain(taskqueue_stub)

    assert "clear complete: {'scanned': 5, 'cleared': 5}" in caplog.text


def test_rerun_is_noop(ndb_stub, taskqueue_stub) -> None:
    for n in range(1, 4):
        _put_team(n, with_location=True)
    _clear_team_normalized_locations()
    updated_after_first = [_fresh(n).updated for n in range(1, 4)]

    totals = _clear_team_normalized_locations()

    assert totals == {"scanned": 3, "cleared": 0}
    updated_after_second = [_fresh(n).updated for n in range(1, 4)]
    assert updated_after_second == updated_after_first
