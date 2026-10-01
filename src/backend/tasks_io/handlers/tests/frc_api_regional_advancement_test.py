from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.futures import InstantFuture
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    TeamRegionalPoolAdvancement,
)
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_regional_rankings_parser import (
    TParsedRegionalAdvancement,
)


def _parsed_advancement() -> TParsedRegionalAdvancement:
    return TParsedRegionalAdvancement(
        advancement={
            "frc254": TeamRegionalPoolAdvancement(
                cmp=True,
                cmp_status=ChampionshipStatus.EVENT_QUALIFIED,
                qualifying_event="2025casj",
                qualifying_award_name="Regional Winners",
            ),
            "frc1678": TeamRegionalPoolAdvancement(
                cmp=False,
                cmp_status=ChampionshipStatus.NOT_INVITED,
            ),
        },
        adjustments={"frc1678": 5},
    )


def test_regional_advancement_bad_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/get/regional_advancement/2020")
    assert resp.status_code == 400
    assert resp.data == b"Invalid year for regional pool"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(DatafeedFMSAPI, "get_regional_rankings")
def test_regional_advancement(
    api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    data = _parsed_advancement()
    api_mock.return_value = InstantFuture(data)

    resp = tasks_client.get("/tasks/get/regional_advancement/2025")
    assert resp.status_code == 200
    assert b"Fetched advancement:" in resp.data
    assert b"Regional Winners" in resp.data
    api_mock.assert_called_once_with(2025)

    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2025))
    assert pool is not None
    assert pool.advancement == data.advancement
    assert pool.adjustments == data.adjustments

    # Rankings are recomputed to pick up the new adjustments
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/regional_champs_pool_rankings_calc/2025"


@mock.patch.object(DatafeedFMSAPI, "get_regional_rankings")
def test_regional_advancement_updates_existing_pool(
    api_mock: mock.Mock,
    tasks_client: Client,
) -> None:
    RegionalChampsPool(
        id=RegionalChampsPool.render_key_name(2025),
        year=2025,
        advancement={},
        adjustments={"frc254": 1},
    ).put()
    data = _parsed_advancement()
    api_mock.return_value = InstantFuture(data)

    resp = tasks_client.get("/tasks/get/regional_advancement/2025")
    assert resp.status_code == 200

    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2025))
    assert pool is not None
    assert pool.year == 2025
    assert pool.advancement == data.advancement
    assert pool.adjustments == data.adjustments


@freeze_time("2026-04-01")
@mock.patch.object(DatafeedFMSAPI, "get_regional_rankings")
def test_regional_advancement_default_year(
    api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    api_mock.return_value = InstantFuture(_parsed_advancement())

    resp = tasks_client.get("/tasks/get/regional_advancement/")
    assert resp.status_code == 200

    api_mock.assert_called_once_with(2026)
    assert (
        RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2026))
        is not None
    )

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/regional_champs_pool_rankings_calc/2026"


@mock.patch.object(DatafeedFMSAPI, "get_regional_rankings")
def test_regional_advancement_no_output_in_taskqueue(
    api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    data = _parsed_advancement()
    api_mock.return_value = InstantFuture(data)

    resp = tasks_client.get(
        "/tasks/get/regional_advancement/2025",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert resp.data == b""

    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2025))
    assert pool is not None
    assert pool.advancement == data.advancement

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
