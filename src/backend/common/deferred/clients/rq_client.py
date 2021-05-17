from redis import Redis

from backend.common.deferred.clients.task_client import TaskClient
from backend.common.deferred.queues.rq_queue import RQTaskQueue


class RQTaskClient(TaskClient[RQTaskQueue]):

    default_service: str

    def __init__(self, *, default_service: str, redis_client: Redis) -> None:
        self.default_service = default_service

        super().__init__(redis_client)

    def queue(self, name) -> RQTaskQueue:
        return RQTaskQueue(
            name, default_service=self.default_service, redis_client=self._client
        )
