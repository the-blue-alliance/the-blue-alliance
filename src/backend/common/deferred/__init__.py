import logging

from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

from flask import request
from google.auth.transport import requests as auth_requests
from google.oauth2 import id_token

from backend.common.deferred.clients.task_client import TaskClient
from backend.common.environment import Environment, EnvironmentMode
from backend.common.redis import RedisClient


_DEFAULT_QUEUE = "default"
_DEFAULT_SERVICE = "default"


def defer(
    obj: Callable,
    *args: Any,
    _client: Optional[TaskClient] = None,
    _target: Optional[str] = None,
    _url: str = "/_ah/queue/deferred",
    _headers: Dict[str, str] = {},
    _queue: str = _DEFAULT_QUEUE,
    **kwargs: Any,
) -> None:
    # TODO: Add support for `countdown`, `eta`, `name`, `retry_options`
    headers = dict({"Content-Type": "application/octet-stream"})
    headers.update(_headers)

    client = _client if _client else _client_for_env()
    queue = client.queue(_queue)

    from backend.common.deferred.tasks.task import Task

    task = Task(obj, *args, **kwargs)

    # Attempt to enqueue on the calling service - this mirrors the previous GAE defer functionality
    service = _target if _target else Environment.service()
    queue.enqueue(task, url=_url, headers=headers, service=service)


def enqueue(
    *,
    url: str,
    headers: Dict[str, str] = {},
    method: Optional[str] = "POST",
    params: Optional[Dict[Any, Any]] = None,
    queue_name: Optional[str] = _DEFAULT_QUEUE,
    target: Optional[str] = None
):
    # TODO: Add support for `name`, `countdown`, `eta`, `retry_options`
    defer(_run_enqueue, url, method, params, _target=target, _headers=headers, _queue=queue_name)


def _run_enqueue(
    url: str,
    method: str,
    params: Optional[Dict[Any, Any]] = None
):
    o = urlparse(url)

    # Do not allow hitting URLs outside of TBA services via enqueue
    if o.netloc:
        logging.error(
            "Detected an attempt to reach an outside server via enqueued task."
        )

    netloc = request.headers.get("X-Appengine-Default-Version-Hostname")
    if not netloc:
        abort(403)

    headers = {}

    # POST requests only support HTTP body parameters
    # GET requests do not support parameters - use a POST request instead
    if method == "POST":
        if params:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif method == "GET":
        pass
    else:
        raise Exception("Unsupported enqueue method - only `GET` and `POST` supported.")

    o = o._replace(scheme=request.scheme, netloc=netloc)

    url = o.geturl()

    # Add an auth header to support service-to-service requests
    token = id_token.fetch_id_token(auth_requests.Request(), url)
    headers = {
        'Authorization': f'Bearer {token}'
    }

    import requests as reqs

    resp = reqs.request(method, url, headers=headers, data=params)
    # Retry via taskqueue if non-200 status code from endpoint
    # Note - errors for 400-range status codes will throw exceptions
    # These can't really be "fixed" but should be monitored for
    resp.raise_for_status()


def _client_for_env() -> TaskClient:
    # If we're running in tests, always return a FakeTestClient
    if Environment.is_unit_test():
        from backend.common.deferred.clients.fake_client import FakeTaskClient

        return FakeTaskClient()

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
