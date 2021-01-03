from backend.common.deferred.clients.rq_client import RQTaskClient
from backend.common.deferred.queues.rq_queue import RQTaskQueue
from backend.common.deferred.tasks.task import Task
from backend.common.redis import RedisClient


class InlineRQTaskQueue(RQTaskQueue):
    """
    A RQ-backed queue, but will run jobs inline
    instead of making a HTTP request callback
    """

    def enqueue(self, task: Task, *args, **kwargs) -> None:
        self._queue.enqueue(task.obj, *task.args, **task.kwargs)


class FakeRQTaskClient(RQTaskClient):
    def queue(self, name) -> InlineRQTaskQueue:
        return InlineRQTaskQueue(
            name, default_service=self.default_service, redis_client=self._client
        )


class FakeTaskClient(FakeRQTaskClient):
    """
    Similar interface to an in-memory RQTaskClient, except:
     - with a stubbed out Redis client
     - and will execute functions inline so we can manually run them
    """

    def __init__(self) -> None:
        from fakeredis import FakeRedis

        super().__init__(
            default_service="test", redis_client=RedisClient.get() or FakeRedis()
        )

    def pending_job_count(self, queue_name: str) -> int:
        return len(self.queue(queue_name).jobs())

    def drain_pending_jobs(self, queue_name: str) -> None:
        jobs = self.queue(queue_name).jobs()
        [j.perform() for j in jobs]
