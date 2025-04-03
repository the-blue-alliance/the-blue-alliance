import datetime
import json
from typing import Dict, Optional
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def create_event(
    official: bool,
    end_date: Optional[datetime.datetime] = None,
    remap_teams: Optional[Dict[str, str]] = None,
) -> Event:
    e = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2019, 4, 1),
        end_date=end_date or datetime.datetime(2019, 4, 3),
        official=official,
        remap_teams=remap_teams,
    )
    e.put()
    return e


def test_enqueue_bad_when(tasks_client: Client) -> None:
    create_event(official=True)
    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/asdf")
    assert resp.status_code == 404


@freeze_time("2019-04-01")
def test_enqueue_current(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/fmsapi_awards/2019casj"


@freeze_time("2019-04-01")
def test_enqueue_current_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get(
        "/tasks/enqueue/fmsapi_awards/now", headers={"X-Appengine-Taskname": "test"}
    )
    assert resp.status_code == 200
    assert resp.data == b""


@freeze_time("2019-04-01")
def test_enqueue_current_official_only(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)

    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/now")
    assert resp.status_code == 200
    assert resp.data != ""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


@freeze_time("2019-04-01")
def test_enqueue_last_day_only(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True, end_date=datetime.datetime(2019, 4, 1))
    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/last_day_only")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1

    expected_keys = ["2019casj"]
    assert [f"/tasks/get/fmsapi_awards/{k}" for k in expected_keys] == [
        t.url for t in tasks
    ]


@freeze_time("2019-04-01")
def test_enqueue_last_day_only_false(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True, end_date=datetime.datetime(2019, 4, 3))
    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/last_day_only")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


@freeze_time("2019-04-01")
def test_enqueue_last_day_only_skips_unofficial(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False, end_date=datetime.datetime(2019, 4, 1))
    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/last_day_only")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_enqueue_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/2019")
    assert resp.status_code == 200
    assert resp.data != ""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/fmsapi_awards/2019casj"


def test_enqueue_year_official_only(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)

    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/2019")
    assert resp.status_code == 200
    assert resp.data != ""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_enqueue_year_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/fmsapi_awards/2020")
    assert resp.status_code == 200
    assert resp.data != ""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_get_bad_event_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/get/fmsapi_awards/asdf")
    assert resp.status_code == 404


def test_get_event_not_found(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/get/fmsapi_awards/2019casj")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_awards")
def test_get_no_awards(api_mock: mock.Mock, tasks_client: Client) -> None:
    e = create_event(official=True)
    api_mock.return_value = InstantFuture([])

    resp = tasks_client.get("/tasks/get/fmsapi_awards/2019casj")
    assert resp.status_code == 200
    api_mock.assert_called_once_with(e)
    assert len(resp.data) > 0


@mock.patch.object(DatafeedFMSAPI, "get_awards")
def test_get_no_output_in_taskqueue(api_mock: mock.Mock, tasks_client: Client) -> None:
    e = create_event(official=True)
    api_mock.return_value = InstantFuture([])

    resp = tasks_client.get(
        "/tasks/get/fmsapi_awards/2019casj", headers={"X-Appengine-Taskname": "test"}
    )
    assert resp.status_code == 200
    api_mock.assert_called_once_with(e)
    assert resp.data == b""


@mock.patch.object(DatafeedFMSAPI, "get_awards")
def test_get_awards_single(api_mock: mock.Mock, tasks_client: Client) -> None:
    e = create_event(official=True)
    api_mock.return_value = InstantFuture(
        [
            Award(
                id="2019casj_1",
                year=2019,
                award_type_enum=AwardType.WINNER,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                team_list=[ndb.Key(Team, "frc254")],
            )
        ]
    )

    resp = tasks_client.get("/tasks/get/fmsapi_awards/2019casj")
    assert resp.status_code == 200
    api_mock.assert_called_once_with(e)

    # Check award gets written
    award = Award.get_by_id("2019casj_1")
    assert award is not None
    assert award.event == e.key

    # Check we created stub teams
    team = Team.get_by_id("frc254")
    assert team is not None
    assert team.team_number == 254

    # Check we created EventTeams
    ets = EventTeam.query(EventTeam.event == e.key).fetch()
    assert len(ets) == 1
    assert ets[0].team == ndb.Key(Team, "frc254")


@mock.patch.object(DatafeedFMSAPI, "get_awards")
def test_get_awards_multiple(api_mock: mock.Mock, tasks_client: Client) -> None:
    e = create_event(official=True)
    api_mock.return_value = InstantFuture(
        [
            Award(
                id="2019casj_1",
                year=2019,
                award_type_enum=AwardType.WINNER,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                team_list=[ndb.Key(Team, "frc254")],
            ),
            Award(
                id="2019casj_0",
                year=2019,
                award_type_enum=AwardType.CHAIRMANS,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                team_list=[ndb.Key(Team, "frc1337")],
            ),
        ]
    )

    resp = tasks_client.get("/tasks/get/fmsapi_awards/2019casj")
    assert resp.status_code == 200
    api_mock.assert_called_once_with(e)

    # Check award gets written
    awards = Award.query(Award.event == e.key).fetch()
    assert len(awards) == 2

    # Check we created stub teams
    assert Team.get_by_id("frc254") is not None
    assert Team.get_by_id("frc1337") is not None

    # Check we created EventTeams
    ets = EventTeam.query(EventTeam.event == e.key).fetch()
    assert len(ets) == 2


@mock.patch.object(DatafeedFMSAPI, "get_awards")
def test_get_awards_team_dedup(api_mock: mock.Mock, tasks_client: Client) -> None:
    e = create_event(official=True)
    api_mock.return_value = InstantFuture(
        [
            Award(
                id="2019casj_1",
                year=2019,
                award_type_enum=AwardType.WINNER,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                team_list=[ndb.Key(Team, "frc254")],
            ),
            Award(
                id="2019casj_0",
                year=2019,
                award_type_enum=AwardType.CHAIRMANS,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                team_list=[ndb.Key(Team, "frc254")],
            ),
        ]
    )

    resp = tasks_client.get("/tasks/get/fmsapi_awards/2019casj")
    assert resp.status_code == 200
    api_mock.assert_called_once_with(e)

    # Check award gets written
    awards = Award.query(Award.event == e.key).fetch()
    assert len(awards) == 2

    # Check we created stub teams
    assert Team.get_by_id("frc254") is not None

    # Check we created EventTeams
    ets = EventTeam.query(EventTeam.event == e.key).fetch()
    assert len(ets) == 1


@mock.patch.object(DatafeedFMSAPI, "get_awards")
def test_get_awards_remapteams(api_mock: mock.Mock, tasks_client: Client) -> None:
    e = create_event(official=True, remap_teams={"frc9000": "frc254B"})
    api_mock.return_value = InstantFuture(
        [
            Award(
                id="2019casj_1",
                year=2019,
                award_type_enum=AwardType.WINNER,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                recipient_json_list=[
                    json.dumps(
                        {"name_str": "", "team_number": "254"},
                    )
                ],
                team_list=[ndb.Key(Team, "frc254")],
            ),
            Award(
                id="2019casj_0",
                year=2019,
                award_type_enum=AwardType.CHAIRMANS,
                event_type_enum=EventType.REGIONAL,
                event=ndb.Key(Event, "2019casj"),
                name_str="Winner",
                recipient_json_list=[
                    json.dumps(
                        {"name_str": "", "team_number": "9000"},
                    )
                ],
                team_list=[ndb.Key(Team, "frc9000")],
            ),
        ]
    )

    resp = tasks_client.get("/tasks/get/fmsapi_awards/2019casj")
    assert resp.status_code == 200
    api_mock.assert_called_once_with(e)

    # Check award gets written
    awards = Award.query(Award.event == e.key).fetch()
    assert len(awards) == 2
    assert awards[0].team_list == [ndb.Key(Team, "frc254B")]
    assert awards[1].team_list == [ndb.Key(Team, "frc254")]

    # Check we created stub teams, but not for the remapped B team
    assert Team.get_by_id("frc254") is not None
    assert Team.get_by_id("frc9000") is None

    # Check we created EventTeams
    ets = EventTeam.query(EventTeam.event == e.key).fetch()
    assert len(ets) == 1
    assert ets[0].team == ndb.Key(Team, "frc254")
