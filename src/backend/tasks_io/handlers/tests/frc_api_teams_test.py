from datetime import datetime, timedelta
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.futures import InstantFuture
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
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
    team_details_mock.return_value = InstantFuture((None, None, None))

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
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc254", team_number=254),
            DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
            Robot(id="frc254_2019", team=ndb.Key(Team, "frc254"), year=2019),
        )
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
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc254", team_number=254),
            DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
            Robot(id="frc254_2019", team=ndb.Key(Team, "frc254"), year=2019),
        )
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
    api_mock.return_value = InstantFuture(
        (
            None,
            None,
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is None
    assert DistrictTeam.query().fetch() == []
    assert Robot.query().fetch() == []


@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details_none(api_mock, tasks_client: Client) -> None:
    api_mock.return_value = InstantFuture(None)
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
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc254", team_number=254),
            None,
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019ne_frc254") is None


@freeze_time("2019-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_none_clears_districtteams(api_mock, tasks_client: Client) -> None:
    DistrictTeam(id="2019ne_frc254", team=ndb.Key(Team, "frc254"), year=2019).put()
    api_mock.return_value = InstantFuture(None)
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we wrote no models
    assert Team.get_by_id("frc254") is None
    assert DistrictTeam.get_by_id("2019ne_frc254") is None


@freeze_time("2019-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_fixes_district_teams(api_mock, tasks_client: Client) -> None:
    # Team moved districts within the same year: the old same-year row
    # should be replaced with the new one the API just confirmed.
    DistrictTeam(id="2019ne_frc254", team=ndb.Key(Team, "frc254"), year=2019).put()
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc254", team_number=254),
            DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    assert Team.get_by_id("frc254") is not None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None
    assert DistrictTeam.get_by_id("2019ne_frc254") is None
    assert Robot.query().fetch() == []


@freeze_time("2019-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_preserves_past_year_district_teams(
    api_mock, tasks_client: Client
) -> None:
    # Past-year DistrictTeams must not be touched by a current-year sync.
    # FIRST's answer for 2019 says nothing about 2018, so leave 2018 alone.
    DistrictTeam(
        id="2018in_frc254",
        district_key=ndb.Key(District, "2018in"),
        team=ndb.Key(Team, "frc254"),
        year=2018,
    ).put()
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc254", team_number=254),
            DistrictTeam(id="2019fim_frc254", team=ndb.Key(Team, "frc254"), year=2019),
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc254")
    assert resp.status_code == 200

    assert DistrictTeam.get_by_id("2018in_frc254") is not None
    assert DistrictTeam.get_by_id("2019fim_frc254") is not None


@freeze_time("2026-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_keeps_district_team_without_eventteams(
    api_mock, tasks_client: Client
) -> None:
    # A team with no EventTeam records yet (e.g., rookies, or early season
    # before events are synced) must still have their DistrictTeam preserved.
    # FIRST's API is the authority on district membership, not EventTeam presence.
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc6921", team_number=6921),
            DistrictTeam(
                id="2026fma_frc6921",
                team=ndb.Key(Team, "frc6921"),
                year=2026,
                district_key=ndb.Key(District, "2026fma"),
            ),
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc6921")
    assert resp.status_code == 200

    assert Team.get_by_id("frc6921") is not None
    assert DistrictTeam.get_by_id("2026fma_frc6921") is not None


@freeze_time("2026-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details_with_year_override(api_mock, tasks_client: Client) -> None:
    # Callers can target a specific year via the ?year= query param. Useful for
    # one-off backfill when a prior year's DistrictTeams are missing.
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc6921", team_number=6921),
            DistrictTeam(
                id="2025fma_frc6921",
                team=ndb.Key(Team, "frc6921"),
                year=2025,
                district_key=ndb.Key(District, "2025fma"),
            ),
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc6921/2025")
    assert resp.status_code == 200

    api_mock.assert_called_once_with(2025, "frc6921")
    assert DistrictTeam.get_by_id("2025fma_frc6921") is not None


@freeze_time("2026-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details_year_override_scoped_to_that_year(
    api_mock, tasks_client: Client
) -> None:
    # A year-overridden call must only reconcile DistrictTeams for that year.
    # Other years' rows must be untouched.
    DistrictTeam(
        id="2026fim_frc6921",
        team=ndb.Key(Team, "frc6921"),
        year=2026,
        district_key=ndb.Key(District, "2026fim"),
    ).put()
    DistrictTeam(
        id="2025ne_frc6921",
        team=ndb.Key(Team, "frc6921"),
        year=2025,
        district_key=ndb.Key(District, "2025ne"),
    ).put()
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc6921", team_number=6921),
            DistrictTeam(
                id="2025fma_frc6921",
                team=ndb.Key(Team, "frc6921"),
                year=2025,
                district_key=ndb.Key(District, "2025fma"),
            ),
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc6921/2025")
    assert resp.status_code == 200

    # 2025 reconciled: new row created, stale same-year row deleted
    assert DistrictTeam.get_by_id("2025fma_frc6921") is not None
    assert DistrictTeam.get_by_id("2025ne_frc6921") is None
    # 2026 untouched
    assert DistrictTeam.get_by_id("2026fim_frc6921") is not None


@freeze_time("2026-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_team_details")
def test_fetch_team_details_historical_year_does_not_overwrite_team(
    api_mock, tasks_client: Client
) -> None:
    # Backfilling a historical year must not clobber current Team metadata
    # (name, nickname, city, etc.) with a stale snapshot. The handler should
    # still reconcile year-scoped rows (DistrictTeam, Robot) but skip the
    # global Team write when year < max_year.
    Team(id="frc6921", team_number=6921, nickname="Current Name").put()
    api_mock.return_value = InstantFuture(
        (
            Team(id="frc6921", team_number=6921, nickname="Stale 2025 Name"),
            DistrictTeam(
                id="2025fma_frc6921",
                team=ndb.Key(Team, "frc6921"),
                year=2025,
                district_key=ndb.Key(District, "2025fma"),
            ),
            None,
        )
    )
    resp = tasks_client.get("/backend-tasks/get/team_details/frc6921/2025")
    assert resp.status_code == 200

    # DistrictTeam for 2025 was created (year-scoped, safe)
    assert DistrictTeam.get_by_id("2025fma_frc6921") is not None
    # Team metadata was NOT overwritten with the stale 2025 snapshot
    current_team = Team.get_by_id("frc6921")
    assert current_team is not None
    assert current_team.nickname == "Current Name"


def test_fetch_team_avatar_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/team_avatar/asdf")
    assert resp.status_code == 400


@mock.patch.object(DatafeedFMSAPI, "get_team_avatar")
def test_fetch_team_avatar(api_mock, tasks_client: Client) -> None:
    api_mock.return_value = InstantFuture(
        (
            [
                Media(
                    id="avatar_media", foreign_key="", media_type_enum=MediaType.AVATAR
                )
            ],
            [],
        )
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
    api_mock.return_value = InstantFuture(
        (
            [
                Media(
                    id="avatar_media", foreign_key="", media_type_enum=MediaType.AVATAR
                )
            ],
            [],
        )
    )
    resp = tasks_client.get(
        "/backend-tasks/get/team_avatar/frc254",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    # Make sure we write models
    assert Media.get_by_id("avatar_media") is not None
