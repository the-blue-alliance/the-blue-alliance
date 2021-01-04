import logging
import re
from unittest.mock import ANY, patch

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common.deferred import _client_for_env, defer
from backend.common.deferred.clients.fake_client import FakeTaskClient
from backend.common.deferred.clients.gcloud_client import GCloudTaskClient
from backend.common.deferred.clients.rq_client import RQTaskClient
from backend.common.deferred.queues.task_queue import TaskQueue
from backend.common.deferred.requests.gcloud_http_request import (
    GCloudHttpTaskRequestConfiguration,
)
from backend.common.deferred.tasks.task import Task


@pytest.fixture
def set_override_tba_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_UNIT_TEST", "false")


@pytest.fixture
def set_project(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "tbatv-prod-hrd")


@pytest.fixture
def set_dev(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")


@pytest.fixture
def set_service(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_SERVICE", "not-default")


@pytest.fixture
def set_tasks_local(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TASKS_MODE", "local")


@pytest.fixture
def set_tasks_remote(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TASKS_MODE", "remote")


@pytest.fixture
def set_redis(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_CACHE_URL", "redis://localhost:1234")


@pytest.fixture
def set_tasks_remote_config(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TASKS_REMOTE_CONFIG_NGROK_URL", "http://1d03c3c73356.ngrok.io")


def test_client_for_env_test():
    client = _client_for_env()
    assert type(client) is FakeTaskClient


def test_client_for_env_no_project(set_override_tba_test):
    with pytest.raises(
        Exception,
        match=re.escape(
            "Environment.project (GOOGLE_CLOUD_PROJECT) unset - should be set in production."
        ),
    ):
        _client_for_env()


def test_client_for_env_production(set_override_tba_test, set_project):
    with patch.object(
        GCloudTaskClient, "__init__", return_value=None
    ) as gcloud_client_init:
        client = _client_for_env()

    gcloud_client_init.assert_called_with("tbatv-prod-hrd")
    assert type(client) is GCloudTaskClient


def test_client_for_env_dev_local_no_redis(
    set_override_tba_test, set_project, set_dev, set_tasks_local
):
    with pytest.raises(Exception, match="Redis is not setup for the environment."):
        _client_for_env()


def test_client_for_env_dev_local(
    set_override_tba_test, set_project, set_dev, set_tasks_local, set_redis
):
    with patch.object(RQTaskClient, "__init__", return_value=None) as rq_client_init:
        client = _client_for_env()

    rq_client_init.assert_called_with(default_service="default", redis_client=ANY)
    assert type(client) is RQTaskClient


def test_client_for_env_dev_local_service(
    set_override_tba_test, set_project, set_dev, set_service, set_tasks_local, set_redis
):
    with patch.object(RQTaskClient, "__init__", return_value=None) as rq_client_init:
        client = _client_for_env()

    rq_client_init.assert_called_with(default_service="not-default", redis_client=ANY)
    assert type(client) is RQTaskClient


def test_client_for_env_dev_remote_fallback_no_redis(
    set_override_tba_test, caplog, set_project, set_dev, set_tasks_remote
):
    with caplog.at_level(logging.WARNING), pytest.raises(
        Exception, match="Redis is not setup for the environment."
    ):
        _client_for_env()

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert (
        record.msg
        == "tasks_remote_config not set in tba_dev_configuration.json. Falling back to RQ task queue. See documentation for configuration instructions."
    )


def test_client_for_env_dev_remote_fallback(
    set_override_tba_test, caplog, set_project, set_dev, set_tasks_remote, set_redis
):
    with patch.object(RQTaskClient, "__init__", return_value=None) as rq_client_init:
        client = _client_for_env()

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert (
        record.msg
        == "tasks_remote_config not set in tba_dev_configuration.json. Falling back to RQ task queue. See documentation for configuration instructions."
    )

    rq_client_init.assert_called_with(default_service="default", redis_client=ANY)
    assert type(client) is RQTaskClient


def test_client_for_env_dev_remote_fallback_service(
    set_override_tba_test,
    caplog,
    set_project,
    set_dev,
    set_tasks_remote,
    set_redis,
    set_service,
):
    with patch.object(RQTaskClient, "__init__", return_value=None) as rq_client_init:
        client = _client_for_env()

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert (
        record.msg
        == "tasks_remote_config not set in tba_dev_configuration.json. Falling back to RQ task queue. See documentation for configuration instructions."
    )

    rq_client_init.assert_called_with(default_service="not-default", redis_client=ANY)
    assert type(client) is RQTaskClient


def test_client_for_env_dev_remote(
    set_override_tba_test, set_dev, set_tasks_remote, set_tasks_remote_config
):
    with patch.object(
        GCloudTaskClient, "__init__", return_value=None
    ) as gcloud_client_init:
        client = _client_for_env()

    gcloud_client_init.assert_called_with(
        "test",
        http_request_configuration=GCloudHttpTaskRequestConfiguration(
            base_url="http://1d03c3c73356.ngrok.io"
        ),
    )
    assert type(client) is GCloudTaskClient


def test_client_for_env_dev_remote_project(
    set_override_tba_test,
    set_project,
    set_dev,
    set_tasks_remote,
    set_tasks_remote_config,
):
    with patch.object(
        GCloudTaskClient, "__init__", return_value=None
    ) as gcloud_client_init:
        client = _client_for_env()

    gcloud_client_init.assert_called_with(
        "tbatv-prod-hrd",
        http_request_configuration=GCloudHttpTaskRequestConfiguration(
            base_url="http://1d03c3c73356.ngrok.io"
        ),
    )
    assert type(client) is GCloudTaskClient


def test_defer_headers_default():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient())
    headers = mock_enqueue.call_args.kwargs["headers"]
    assert headers == {"Content-Type": "application/octet-stream"}


def test_defer_headers():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient(), _headers={"X-Header": "abc"})
    headers = mock_enqueue.call_args.kwargs["headers"]
    assert headers == {"Content-Type": "application/octet-stream", "X-Header": "abc"}


def test_defer_client_env():
    from backend.common import deferred

    with patch.object(deferred, "_client_for_env") as mock_client_for_env:
        defer(print)
    mock_client_for_env.assert_called()


def test_defer_client():
    from backend.common import deferred

    with patch.object(deferred, "_client_for_env") as mock_client_for_env:
        defer(print, _client=FakeTaskClient())
    mock_client_for_env.assert_not_called()


def test_defer_queue_default():
    client = FakeTaskClient()
    with patch.object(client, "queue") as mock_queue:
        defer(print, _client=client)
    mock_queue.assert_called_with("default")


def test_defer_queue():
    client = FakeTaskClient()
    with patch.object(client, "queue") as mock_queue:
        defer(print, _client=client, _queue="my-queue")
    mock_queue.assert_called_with("my-queue")


def test_defer_enqueue_url_default():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient())
    url = mock_enqueue.call_args.kwargs["url"]
    assert url == "/_ah/queue/deferred"


def test_defer_enqueue_url():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient(), _url="/my/custom/url")
    url = mock_enqueue.call_args.kwargs["url"]
    assert url == "/my/custom/url"


def test_defer_enqueue_target_default():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient())
    service = mock_enqueue.call_args.kwargs["service"]
    assert service is None


def test_defer_enqueue_target():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient(), _target="tbans")
    service = mock_enqueue.call_args.kwargs["service"]
    assert service == "tbans"


def test_defer_enqueue_target_environment(set_service):
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient())
    service = mock_enqueue.call_args.kwargs["service"]
    assert service == "not-default"


def test_defer_enqueue_target_none():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient())
    service = mock_enqueue.call_args.kwargs["service"]
    assert service is None


def test_defer_enqueue_target_environment_explicit(set_service):
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient(), _target="tbans")
    service = mock_enqueue.call_args.kwargs["service"]
    assert service == "tbans"


def test_defer_enqueue_task_simple():
    with patch.object(TaskQueue, "enqueue") as mock_enqueue:
        defer(print, _client=FakeTaskClient())
    task = mock_enqueue.call_args[0][0]
    assert type(task) is Task
