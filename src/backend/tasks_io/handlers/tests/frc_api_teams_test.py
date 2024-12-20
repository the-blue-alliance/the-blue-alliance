from datetime import datetime, timedelta
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_enqueue_rolling(
    team_details_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    team_details_mock.return_value = (None, None, None)

    # Create 10 teams
    [
        Team(
            id=f"frc{t}",
            team_number=t,
        ).put()
        for t in range(1, 11)
    ]

    with freeze_time(datetime.now()) as frozen_time:
        # Over a 14 day period, we should enqueue them each
        for _ in range(15):
            frozen_time.tick(delta=timedelta(days=1))
            resp = tasks_client.get("/tasks/enqueue/fmsapi_team_details_rolling")
            assert resp.status_code == 200
            assert len(resp.data) > 0

        tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")

        # Each team we created should have at least one task
        enqueued_team_numbers = set([int(t.url[35:]) for t in tasks])
        assert set(range(1, 11)) == enqueued_team_numbers

        for task in tasks:
            task_resp = tasks_client.get(task.url)
            assert task_resp.status_code == 200


@freeze_time("2020-4-2")
def test_enqueue_rolling_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    [
        Team(
            id=f"frc{t}",
            team_number=t,
        ).put()
        for t in range(1, 15)
    ]

    resp = tasks_client.get(
        "/tasks/enqueue/fmsapi_team_details_rolling",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) > 0


def test_fetch_team_details_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/team_details/asdf")
    assert resp.status_code == 400


@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details(api_mock, tasks_client: Client) -> None:
    EventTeam(
        id="2019fim_frc254",
        event=ndb.Key("Event", "2019fim"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    api_mock.return_value = (
        Team(id="frc254", team_number=254),
        DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
        Robot(id="frc254_2019", team=ndb.Key(Team, "frc254"), year=2019),
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None
    assert Robot.get_by_id("frc254_2019") is not None


@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    EventTeam(
        id="2019fim_frc254",
        event=ndb.Key("Event", "2019fim"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    api_mock.return_value = (
        Team(id="frc254", team_number=254),
        DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
        Robot(id="frc254_2019", team=ndb.Key(Team, "frc254"), year=2019),
    )
    resp = tasks_client.get(
        "/backend-tasks/get/team_details/frc254",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    # Make sure we write models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None
    assert Robot.get_by_id("frc254_2019") is not None


@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details_empty(api_mock, tasks_client: Client) -> None:
    api_mock.return_value = (
        None,
        None,
        None,
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is None
    assert DistrictTeam.query().fetch() == []
    assert Robot.query().fetch() == []


@freeze_time("2019-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_clears_districtteams(api_mock, tasks_client: Client) -> None:
    DistrictTeam(id="2019ne_frc254", team=ndb.Key(Team, "frc254"), year=2019).put()
    api_mock.return_value = (
        Team(id="frc254", team_number=254),
        None,
        None,
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019ne_frc254") is None


@freeze_time("2019-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_fixes_district_teams(api_mock, tasks_client: Client) -> None:
    DistrictTeam(id="2019ne_frc254", team=ndb.Key(Team, "frc254"), year=2019).put()
    EventTeam(
        id="2019ne_frc254",
        event=ndb.Key("Event", "2019ne"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    api_mock.return_value = (
        Team(id="frc254", team_number=254),
        DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
        None,
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None
    assert DistrictTeam.get_by_id("2019ne_frc254") is None
    assert Robot.query().fetch() == []


@freeze_time("2019-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_removes_bad_district_teams(api_mock, tasks_client: Client) -> None:
    # Create a bad DistrictTeam, from a previous year, with no events for that team
    DistrictTeam(
        id="2018in_frc254",
        district_key=ndb.Key(District, "2018in"),
        team=ndb.Key(Team, "frc254"),
        year=2018,
    ).put()
    EventTeam(
        id="2019fim_frc254",
        event=ndb.Key("Event", "2019fim"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    api_mock.return_value = (
        Team(id="frc254", team_number=254),
        DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
        None,
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2018in_frc254") is None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None
    assert DistrictTeam.get_by_id("2019ne_frc254") is None
    assert Robot.query().fetch() == []


def test_fetch_team_avatar_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/team_avatar/asdf")
    assert resp.status_code == 400


@mock.patch.object(DatafeedFMSAPI, "get_team_avatar")
def test_fetch_team_avatar(api_mock, tasks_client: Client) -> None:
    api_mock.return_value = (
        [Media(id="avatar_media", foreign_key="", media_type_enum=MediaType.AVATAR)],
        [],
    )
    resp = tasks_client.get("/backend-tasks/get/team_avatar/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write models
    assert Media.get_by_id("avatar_media") is not None


@mock.patch.object(DatafeedFMSAPI, "get_team_avatar")
def test_fetch_team_avatar_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    api_mock.return_value = (
        [Media(id="avatar_media", foreign_key="", media_type_enum=MediaType.AVATAR)],
        [],
    )
    resp = tasks_client.get(
        "/backend-tasks/get/team_avatar/frc254",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    # Make sure we write models
    assert Media.get_by_id("avatar_media") is not None
