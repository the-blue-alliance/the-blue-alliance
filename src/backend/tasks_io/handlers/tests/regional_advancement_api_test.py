from unittest import mock

import pytest
from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.futures import InstantFuture
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.common.sitevars.regional_advancement_api_secrets import (
    ContentType as RegionalAdvancementAPISecretsContentType,
    RegionalAdvancementApiSecret,
)
from backend.tasks_io.datafeeds.datafeed_regional_advancement import (
    RegionalChampsAdvancement,
)
from backend.tasks_io.datafeeds.parsers.ra.regional_advancement_parser import (
    TParsedRegionalAdvancement,
)


@pytest.fixture(autouse=True)
def ra_api_secrets(ndb_stub) -> None:
    RegionalAdvancementApiSecret.put(
        RegionalAdvancementAPISecretsContentType(url_format="/{year}")
    )


@mock.patch.object(RegionalChampsAdvancement, "fetch_async")
def test_get_bad_season(
    ra_api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_client.get("/tasks/get/regional_advancement/2019")
    assert resp.status_code == 400
    ra_api_mock.assert_not_called()


@freeze_time("2025-04-01")
@mock.patch.object(RegionalChampsAdvancement, "fetch_async")
def test_get_current_season(
    ra_api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    api_return = TParsedRegionalAdvancement(
        advancement={},
        adjustments={},
    )
    ra_api_mock.return_value = InstantFuture(api_return)

    resp = tasks_client.get("/tasks/get/regional_advancement/")
    assert resp.status_code == 200

    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2025))
    assert pool is not None
    assert pool.advancement == api_return.advancement
    assert pool.adjustments == api_return.adjustments

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/regional_champs_pool_rankings_calc/2025"
    for task in tasks:
        r = tasks_client.get(task.url)
        assert r.status_code == 200


@mock.patch.object(RegionalChampsAdvancement, "fetch_async")
def test_get_explicit_season(
    ra_api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    api_return = TParsedRegionalAdvancement(
        advancement={},
        adjustments={},
    )
    ra_api_mock.return_value = InstantFuture(api_return)

    resp = tasks_client.get("/tasks/get/regional_advancement/2025")
    assert resp.status_code == 200

    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2025))
    assert pool is not None
    assert pool.advancement == api_return.advancement
    assert pool.adjustments == api_return.adjustments

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/regional_champs_pool_rankings_calc/2025"
    for task in tasks:
        r = tasks_client.get(task.url)
        assert r.status_code == 200


@mock.patch.object(RegionalChampsAdvancement, "fetch_async")
def test_get_explicit_season_doest_write_out_in_taskqueue(
    ra_api_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    api_return = TParsedRegionalAdvancement(
        advancement={},
        adjustments={},
    )
    ra_api_mock.return_value = InstantFuture(api_return)

    resp = tasks_client.get(
        "/tasks/get/regional_advancement/2025",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(2025))
    assert pool is not None
    assert pool.advancement == api_return.advancement
    assert pool.adjustments == api_return.adjustments

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/regional_champs_pool_rankings_calc/2025"
    for task in tasks:
        r = tasks_client.get(task.url)
        assert r.status_code == 200
