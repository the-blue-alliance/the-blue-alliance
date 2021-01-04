from typing import Dict, Optional

from redis import Redis

from backend.common.deferred.queues.task_queue import TaskQueue
from backend.common.deferred.requests.rq_request import RQTaskRequest
from backend.common.deferred.tasks.task import Task


class RQTaskQueue(TaskQueue[RQTaskRequest]):
    def __init__(self, name: str, *, default_service: str, redis_client: Redis) -> None:
        self.default_service = default_service

        from rq import Queue as RQQueue

        self._queue = RQQueue(name, connection=redis_client)

        super().__init__(name)

    def _task_request(
        self,
        url: str,
        headers: Dict[str, str],
        body: bytes,
        service: Optional[str] = None,
    ) -> RQTaskRequest:
        service = service if service else self.default_service
        return RQTaskRequest(url, headers, body, service)

    def _enqueue(self, request: RQTaskRequest) -> None:
        import requests

        self._queue.enqueue(
            requests.post, url=request.url, data=request.body, headers=request.headers
        )

    def jobs(self):
        return self._queue.jobs


class InlineRQTaskQueue(RQTaskQueue):
    """
    A RQ-backed queue, but will run jobs inline
    instead of making a HTTP request callback
    """

    def enqueue(self, task: Task, *args, **kwargs) -> None:
        self._queue.enqueue(task.obj, *task.args, **task.kwargs)
