import logging
import os
from typing import Any, Callable, Dict, Optional

from backend.common.deferred.clients.task_client import TaskClient
from backend.common.environment import Environment
from backend.common.redis import RedisClient


_TASKQUEUE_HEADERS = {"Content-Type": "application/octet-stream"}
_DEFAULT_URL = "/_ah/queue/deferred"
_DEFAULT_QUEUE = "default"
_DEFAULT_SERVICE = "default"


def defer(
    obj: Callable,
    *args: Any,
    _client: Optional[TaskClient] = None,
    _target: Optional[str] = None,
    _url: str = _DEFAULT_URL,
    _headers: Dict[Any, Any] = {},
    _queue: str = _DEFAULT_QUEUE,
    **kwargs: Any,
) -> None:
    # TODO: Add support for `countdown`, `eta`, `name`, `retry_options`
    headers = dict(_TASKQUEUE_HEADERS)
    headers.update(_headers)

    client = _client if _client else _client_for_env()
    queue = client.queue(_queue)

    from backend.common.deferred.tasks.task import Task

    task = Task(obj, *args, **kwargs)

    # Attempt to enqueue on the calling service - this mirrors the previous GAE defer functionality
    service = _target if _target else Environment.service()
    queue.enqueue(task, url=_url, headers=headers, service=service)


def _client_for_env() -> TaskClient:
    # If we're running in tests, always return a FakeTestClient
    if os.environ.get("TBA_UNIT_TEST", None) == "true":
        from backend.common.deferred.clients.fake_client import FakeTaskClient

        return FakeTaskClient()

    from backend.common.environment import EnvironmentMode
    from backend.common.deferred.clients.gcloud_client import GCloudTaskClient
    from backend.common.deferred.clients.rq_client import RQTaskClient
    from backend.common.deferred.requests.gcloud_http_request import (
        GCloudHttpTaskRequestConfiguration,
    )

    project = Environment.project()

    if Environment.is_dev():
        service = Environment.service()
        service = service if service else _DEFAULT_SERVICE

        # If in dev - use RQ for local task env mode, GCloud for remote task env mode
        task_mode = Environment.tasks_mode()
        if task_mode == EnvironmentMode.LOCAL:
            redis_client = RedisClient.get()
            if not redis_client:
                raise Exception("Redis is not setup for the environment.")

            return RQTaskClient(default_service=service, redis_client=redis_client)
        elif task_mode == EnvironmentMode.REMOTE:
            remote_config = Environment.tasks_remote_config()
            if remote_config and remote_config.ngrok_url:
                project = project if project else "test"
                return GCloudTaskClient(
                    project,
                    http_request_configuration=GCloudHttpTaskRequestConfiguration(
                        remote_config.ngrok_url
                    ),
                )
            else:
                logging.warning(
                    "tasks_remote_config not set in tba_dev_configuration.json. Falling back to RQ task queue. See documentation for configuration instructions."
                )
                redis_client = RedisClient.get()
                if not redis_client:
                    raise Exception("Redis is not setup for the environment.")

                return RQTaskClient(default_service=service, redis_client=redis_client)
        else:
            raise Exception(f"Unsupported EnvironmentMode.task_mode f{task_mode}.")

    # If we're in prod - always run `deferred` in the GCloud task queue
    if not project:
        raise Exception(
            "Environment.project (GOOGLE_CLOUD_PROJECT) unset - should be set in production."
        )

    return GCloudTaskClient(project)
