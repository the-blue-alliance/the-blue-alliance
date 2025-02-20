import datetime
from unittest import mock

from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.futures import InstantFuture
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def create_event() -> Event:
    e = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        start_date=datetime.datetime(2019, 4, 1),
        end_date=datetime.datetime(2019, 4, 3),
        event_type_enum=EventType.REGIONAL,
    )
    return e


def create_district() -> District:
    return District(
        id="2019fim",
        year=2019,
        abbreviation="fim",
    )


def test_enqueue_bad_key(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/backend-tasks/enqueue/event_details/abc")
    assert resp.status_code == 400

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_enqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/backend-tasks/enqueue/event_details/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks/get/event_details/2019casj"


def test_enqueue_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/backend-tasks/enqueue/event_details/2019casj",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks/get/event_details/2019casj"


def test_get_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/event_details/asdf")
    assert resp.status_code == 400


@mock.patch.object(DatafeedFMSAPI, "get_event_team_avatars")
@mock.patch.object(DatafeedFMSAPI, "get_event_teams")
@mock.patch.object(DatafeedFMSAPI, "get_event_details")
def test_get_event_details(
    event_mock, teams_mock, avatars_mock, tasks_client: Client
) -> None:
    event_mock.return_value = InstantFuture(([create_event()], [create_district()]))
    teams_mock.return_value = InstantFuture([])
    avatars_mock.return_value = InstantFuture(([], []))

    resp = tasks_client.get("/backend-tasks/get/event_details/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write models
    assert Event.get_by_id("2019casj") is not None
    assert District.get_by_id("2019fim") is not None


@mock.patch.object(SeasonHelper, "get_max_year", return_value=2019)
@mock.patch.object(DatafeedFMSAPI, "get_event_team_avatars")
@mock.patch.object(DatafeedFMSAPI, "get_event_teams")
@mock.patch.object(DatafeedFMSAPI, "get_event_details")
def test_get_event_details_writes_teams(
    event_mock, teams_mock, avatars_mock, max_year_mock, tasks_client: Client
) -> None:
    event_mock.return_value = InstantFuture(([create_event()], [create_district()]))
    teams_mock.return_value = InstantFuture(
        [
            (
                Team(id="frc254", team_number=254),
                DistrictTeam(id="2019fim_frc254"),
                Robot(id="frc254_2019", team=ndb.Key(Team, "frc254"), year=2019),
            ),
        ]
    )
    avatars_mock.return_value = InstantFuture(
        (
            [
                Media(
                    id="avatar_media", foreign_key="", media_type_enum=MediaType.AVATAR
                )
            ],
            [],
        )
    )
    resp = tasks_client.get("/backend-tasks/get/event_details/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None
    assert Robot.get_by_id("frc254_2019") is not None
    assert EventTeam.get_by_id("2019casj_frc254") is not None
    assert Media.get_by_id("avatar_media") is not None


@mock.patch.object(SeasonHelper, "get_max_year", return_value=2019)
@mock.patch.object(DatafeedFMSAPI, "get_event_team_avatars")
@mock.patch.object(DatafeedFMSAPI, "get_event_teams")
@mock.patch.object(DatafeedFMSAPI, "get_event_details")
def test_get_event_details_clears_eventteams(
    event_mock, teams_mock, avatars_mock, max_year_mock, tasks_client: Client
) -> None:
    event_mock.return_value = InstantFuture(([create_event()], [create_district()]))
    avatars_mock.return_value = InstantFuture(([], []))
    teams_mock.return_value = InstantFuture(
        [
            (
                Team(id="frc254", team_number=254),
                None,  # DistrictTeam
                None,  # Robot
            ),
        ]
    )

    EventTeam(
        id="2019casj_frc900",
        event=ndb.Key(Event, "2019casj"),
        team=ndb.Key(Team, "frc9000"),
        year=2019,
    ).put()
    EventTeam(
        id="2019casj_frc9001",
        event=ndb.Key(Event, "2019casj"),
        team=ndb.Key(Team, "frc9001"),
        year=2019,
    ).put()
    Award(
        id="2019casj_0",
        year=2019,
        award_type_enum=AwardType.CHAIRMANS,
        name_str="Charimans",
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2019casj"),
        team_list=[ndb.Key(Team, "frc9000")],
    ).put()

    resp = tasks_client.get("/backend-tasks/get/event_details/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we clear eventteams, except for those who also won an award
    ets = EventTeam.query(EventTeam.event == ndb.Key(Event, "2019casj")).fetch()
    assert {"frc254", "frc9000"} == {et.team.string_id() for et in ets}


@mock.patch.object(SeasonHelper, "get_max_year", return_value=2019)
@mock.patch.object(ChampsRegistrationHacks, "should_skip_eventteams", return_value=True)
@mock.patch.object(
    DatafeedFMSAPI, "get_event_team_avatars", return_value=InstantFuture(([], []))
)
@mock.patch.object(DatafeedFMSAPI, "get_event_teams")
@mock.patch.object(DatafeedFMSAPI, "get_event_details")
def test_get_event_details_skip_eventteams(
    event_mock,
    teams_mock,
    avatars_mock,
    max_year_mock,
    sv_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    event_mock.return_value = InstantFuture(([create_event()], []))
    teams_mock.return_value = InstantFuture(
        [
            (
                Team(id="frc254", team_number=254),
                None,
                None,
            ),
        ]
    )
    resp = tasks_client.get("/backend-tasks/get/event_details/2019casj")
    assert resp.status_code == 200

    # Make sure we don't write any EventTeams
    assert EventTeam.query(EventTeam.event == ndb.Key(Event, "2019casj")).count() == 0

    # but make sure we enqueue a task to compute them using local data
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/eventteam_update/2019casj?allow_deletes=True"


@mock.patch.object(DatafeedFMSAPI, "get_event_team_avatars")
@mock.patch.object(DatafeedFMSAPI, "get_event_teams")
@mock.patch.object(DatafeedFMSAPI, "get_event_details")
def test_get_event_details_no_output_in_taskqueue(
    event_mock, teams_mock, avatars_mock, tasks_client: Client
) -> None:
    event_mock.return_value = InstantFuture(([create_event()], []))
    teams_mock.return_value = InstantFuture([])
    avatars_mock.return_value = InstantFuture(([], []))

    resp = tasks_client.get(
        "/backend-tasks/get/event_details/2019casj",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
