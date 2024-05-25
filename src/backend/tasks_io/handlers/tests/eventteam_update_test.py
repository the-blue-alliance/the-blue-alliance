import datetime
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.event_team_updater import EventTeamUpdater
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


def test_enqueue_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/eventteam_update/asdf")
    assert resp.status_code == 404


def test_enqueue_invalid_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/eventteam_update/1965")
    assert resp.status_code == 404


@freeze_time("2023-01-01")
def test_enqueue_current_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    ).put()

    resp = tasks_client.get("/tasks/math/enqueue/eventteam_update/current")
    assert resp.status_code == 200
    assert b"Enqueued for 1 events!" in resp.data
    assert b"2023test" in resp.data

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/eventteam_update/2023test"


@freeze_time("2023-01-01")
def test_enqueue_explicit_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    ).put()

    resp = tasks_client.get("/tasks/math/enqueue/eventteam_update/2023")
    assert resp.status_code == 200
    assert b"Enqueued for 1 events!" in resp.data
    assert b"2023test" in resp.data

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/eventteam_update/2023test"


@freeze_time("2023-01-01")
def test_enqueue_no_output_in_taskqueue(tasks_client: Client) -> None:
    Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    ).put()

    resp = tasks_client.get(
        "/tasks/math/enqueue/eventteam_update/current",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_update_bad_key_format(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/eventteam_update/asdf")
    assert resp.status_code == 404


def test_update_bad_event(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/eventteam_update/2023test")
    assert resp.status_code == 404


@mock.patch.object(EventTeamUpdater, "update")
def test_update_adds_eventteams(mock_update, tasks_client: Client) -> None:
    team = Team(
        id="frc1124",
        team_number=1124,
    )
    team.put()
    event = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    )
    event.put()

    expected_eventteam = EventTeam(
        id="2023test_frc1124", event=event.key, team=team.key, year=2023
    )
    mock_update.return_value = (
        [],
        [expected_eventteam],
        {},
    )

    resp = tasks_client.get(
        "/tasks/math/do/eventteam_update/2023test",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


@mock.patch.object(EventTeamUpdater, "update")
def test_update_no_output_in_taskqueue(mock_update, tasks_client: Client) -> None:
    team = Team(
        id="frc1124",
        team_number=1124,
    )
    team.put()
    event = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    )
    event.put()

    expected_eventteam = EventTeam(
        id="2023test_frc1124", event=event.key, team=team.key, year=2023
    )
    mock_update.return_value = (
        [],
        [expected_eventteam],
        {},
    )

    resp = tasks_client.get("/tasks/math/do/eventteam_update/2023test")
    assert resp.status_code == 200
    assert b"Got [ 1 ] EventTeams written!" in resp.data
    assert b"2023test_frc1124" in resp.data

    mock_update.assert_called_once_with("2023test", False)

    eventteams_written = EventTeam.query(EventTeam.event == event.key).fetch()
    assert eventteams_written == [expected_eventteam]


@mock.patch.object(EventTeamUpdater, "update")
def test_update_skips_teams_which_dont_exist(mock_update, tasks_client: Client) -> None:
    event = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    )
    event.put()

    eventteam = EventTeam(
        id="2023test_frc1124", event=event.key, team=ndb.Key(Team, "frc1124"), year=2023
    )
    mock_update.return_value = (
        [],
        [eventteam],
        {},
    )

    resp = tasks_client.get("/tasks/math/do/eventteam_update/2023test")
    assert resp.status_code == 200

    mock_update.assert_called_once_with("2023test", False)

    eventteams_written = EventTeam.query(EventTeam.event == event.key).fetch()
    assert eventteams_written == []


@mock.patch.object(EventTeamUpdater, "update")
def test_update_force_delete_param(mock_update, tasks_client: Client) -> None:
    event = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    )
    event.put()

    mock_update.return_value = (
        [],
        [],
        {},
    )

    resp = tasks_client.get(
        "/tasks/math/do/eventteam_update/2023test", query_string={"allow_deletes": True}
    )
    assert resp.status_code == 200

    mock_update.assert_called_once_with("2023test", True)


@mock.patch.object(EventTeamUpdater, "update")
def test_update_deletes_eventteams(mock_update, tasks_client: Client) -> None:
    team = Team(
        id="frc1124",
        team_number=1124,
    )
    team.put()
    event = Event(
        id="2023test",
        year=2023,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2023, 4, 1),
        end_date=datetime.datetime(2023, 4, 4),
    )
    event.put()
    eventteam = EventTeam(
        id="2023test_frc1124",
        team=team.key,
        event=event.key,
        year=2023,
    )
    eventteam.put()

    mock_update.return_value = (
        [],
        [],
        {eventteam.key},
    )

    resp = tasks_client.get(
        "/tasks/math/do/eventteam_update/2023test", query_string={"allow_deletes": True}
    )
    assert resp.status_code == 200

    mock_update.assert_called_once_with("2023test", True)

    eventteams = EventTeam.query(EventTeam.event == event.key).fetch()
    assert eventteams == []
    assert eventteam.key.get() is None
