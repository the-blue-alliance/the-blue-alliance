from typing import List
from unittest import mock

import pytest
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.predictions_v2 import pipeline
from backend.common.models.event import Event
from backend.common.sitevars.predictions_v2_config import PredictionsV2Config
from backend.tasks_cpu.handlers import predictions_v2


def _tasks(stub: testbed.taskqueue_stub.TaskQueueServiceStub) -> List:
    return stub.get_filtered_tasks(queue_names="predictions-v2")


@pytest.fixture
def enabled() -> None:
    PredictionsV2Config.put({"enabled": True})


@pytest.fixture
def active_events(monkeypatch: pytest.MonkeyPatch) -> List[Event]:
    events = [
        Event(
            id="2024casj",
            year=2024,
            event_short="casj",
            event_type_enum=EventType.REGIONAL,
        ),
        Event(
            id="2024cc",
            year=2024,
            event_short="cc",
            event_type_enum=EventType.OFFSEASON,
        ),
    ]
    for e in events:
        e.put()
    monkeypatch.setattr(EventHelper, "events_within_a_day", lambda: events)
    return events


def test_disabled_by_default(
    tasks_cpu_client: Client, taskqueue_stub, active_events
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/predictions_v2/advance")
    assert resp.status_code == 200
    assert b"disabled" in resp.data
    assert _tasks(taskqueue_stub) == []
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/predictions_v2/advance/2024")
    assert b"disabled" in resp.data


def test_enqueue_advance_only_with_changes(
    tasks_cpu_client: Client, taskqueue_stub, enabled, active_events
) -> None:
    with mock.patch.object(pipeline, "needs_update", return_value=False):
        tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/predictions_v2/advance")
    assert _tasks(taskqueue_stub) == []

    with mock.patch.object(pipeline, "needs_update", return_value=True):
        tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/predictions_v2/advance")
        # A second trigger in the same time bucket is deduplicated by the task name.
        tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/predictions_v2/advance")
    tasks = _tasks(taskqueue_stub)
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/predictions_v2/advance/2024"
    assert tasks[0].name.startswith("predictions_v2_advance_2024_")


def test_do_advance_runs_the_pipeline_on_active_events(
    tasks_cpu_client: Client, enabled, active_events
) -> None:
    with mock.patch.object(pipeline, "advance", return_value={"2024casj"}) as advance:
        resp = tasks_cpu_client.get(
            "/backend-tasks-b2/do/math/predictions_v2/advance/2024"
        )
    assert resp.status_code == 200
    advance.assert_called_once()
    season, events = advance.call_args[0]
    assert season == 2024
    assert [e.key_name for e in events] == ["2024casj", "2024cc"]


def test_do_advance_requests_a_rebuild_once(
    tasks_cpu_client: Client, taskqueue_stub, enabled, active_events
) -> None:
    with mock.patch.object(
        pipeline, "advance", side_effect=pipeline.NeedsRebuild("stale")
    ):
        tasks_cpu_client.get("/backend-tasks-b2/do/math/predictions_v2/advance/2024")
        tasks_cpu_client.get("/backend-tasks-b2/do/math/predictions_v2/advance/2024")
    tasks = _tasks(taskqueue_stub)
    assert len(tasks) == 1
    assert tasks[0].url == (
        f"/backend-tasks-b2/do/math/predictions_v2/rebuild/{pipeline.FIRST_SEASON}?chain=1"
    )


def test_reconcile_checks_every_event_of_the_season(
    tasks_cpu_client: Client, taskqueue_stub, enabled, active_events
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/predictions_v2/reconcile/2024"
    )
    assert resp.status_code == 200
    assert [t.url for t in _tasks(taskqueue_stub)] == [
        "/backend-tasks-b2/do/math/predictions_v2/reconcile/2024"
    ]
    with mock.patch.object(pipeline, "advance", return_value=set()) as advance:
        tasks_cpu_client.get("/backend-tasks-b2/do/math/predictions_v2/reconcile/2024")
    season, events = advance.call_args[0]
    assert season == 2024
    assert sorted(e.key_name for e in events) == ["2024casj", "2024cc"]


def test_rebuild_chains_to_the_next_season(
    tasks_cpu_client: Client, taskqueue_stub, enabled, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(predictions_v2.SeasonHelper, "get_max_year", lambda: 2025)
    tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/predictions_v2/rebuild/2024?chain=1"
    )
    assert [t.url for t in _tasks(taskqueue_stub)] == [
        "/backend-tasks-b2/do/math/predictions_v2/rebuild/2024?chain=1"
    ]
    with mock.patch.object(pipeline, "rebuild") as rebuild:
        tasks_cpu_client.get(
            "/backend-tasks-b2/do/math/predictions_v2/rebuild/2024?chain=1"
        )
        tasks_cpu_client.get(
            "/backend-tasks-b2/do/math/predictions_v2/rebuild/2025?chain=1"
        )
    assert [c.args for c in rebuild.call_args_list] == [(2024,), (2025,)]
    # 2025 is the last season: no further task.
    assert [t.url for t in _tasks(taskqueue_stub)][1:] == [
        "/backend-tasks-b2/do/math/predictions_v2/rebuild/2025?chain=1"
    ]
