from unittest import mock

from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.playoff_advancement_helper import (
    PlayoffAdvancement,
    PlayoffAdvancementHelper,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_playoff_advancement import EventPlayoffAdvancement
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_status import EventTeamStatus
from backend.common.models.team import Team


@mock.patch.object(FirebasePusher, "update_live_events")
def test_update_live_events(update_mock: mock.Mock, tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/update_live_events")
    assert resp.status_code == 200

    update_mock.assert_called_once()


def test_enqueue_eventteam_status_bad_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/asdf")
    assert resp.status_code == 404


def test_enqueue_eventteam_status_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: []"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_eventteam_status_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/math/enqueue/event_team_status/2020",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert resp.data == b""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_eventteam_status(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: ['2020test']"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1


def test_enqueue_eventteam_status_all(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/all")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == len(SeasonHelper.get_valid_years())

    task_urls = {t.url for t in tasks}
    expected_urls = {
        f"/tasks/math/enqueue/event_team_status/{y}"
        for y in SeasonHelper.get_valid_years()
    }
    assert task_urls == expected_urls


def test_do_eventteam_status_not_found(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/event_team_status/asdf")
    assert resp.status_code == 404

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(EventTeamStatusHelper, "generate_team_at_event_status")
def test_do_eventteam_status(
    status_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventTeam(
        id="2020test_frc254",
        year=2020,
        event=ndb.Key(Event, "2020test"),
        team=ndb.Key(Team, "frc254"),
    ).put()
    status = EventTeamStatus(
        qual=None,
        playoff=None,
        alliance=None,
        last_match_key=None,
        next_match_key=None,
    )
    status_mock.return_value = status

    resp = tasks_client.get("/tasks/math/do/event_team_status/2020test")
    assert resp.status_code == 200
    assert resp.data == b"Finished calculating event team statuses for: 2020test"

    et = EventTeam.get_by_id("2020test_frc254")
    assert et is not None
    assert et.status == status


def test_enqueue_playoff_advancement_all(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/playoff_advancement_update/all")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == len(SeasonHelper.get_valid_years())

    task_urls = {t.url for t in tasks}
    expected_urls = {
        f"/tasks/math/enqueue/playoff_advancement_update/{y}"
        for y in SeasonHelper.get_valid_years()
    }
    assert task_urls == expected_urls


def test_enqueue_playoff_advancement_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/playoff_advancement_update/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/playoff_advancement_update/2020test"


def test_enqueue_playoff_advancement_no_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/playoff_advancement_update/asdf")
    assert resp.status_code == 404

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_playoff_advancement(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/playoff_advancement_update/2020test")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued playoff advancement calc for 2020test"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1


def test_calc_playoff_advancement_no_event(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/playoff_advancement_update/asdf")
    assert resp.status_code == 404


@mock.patch.object(PlayoffAdvancementHelper, "generate_playoff_advancement")
def test_calc_playoff_advancement(calc_mock: mock.Mock, tasks_client: Client) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    advancement = PlayoffAdvancement(
        bracket_table={},
        playoff_advancement={},
        double_elim_matches={},
        playoff_template=None,
    )
    calc_mock.return_value = advancement
    resp = tasks_client.get("/tasks/math/do/playoff_advancement_update/2020test")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we set the EventDetails
    ed = EventDetails.get_by_id("2020test")
    assert ed is not None
    assert ed.playoff_advancement == EventPlayoffAdvancement(
        advancement={},
        bracket={},
    )
