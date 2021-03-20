from backend.common.deferred.clients.rq_client import RQTaskClient
from backend.common.deferred.queues.fake_queue import FakeTaskQueue


# Similar interface to an in-memory RQTaskClient, except with a stubbed out Redis client
class FakeTaskClient(RQTaskClient):

    _instance = None
    _redis = None

    def __new__(cls):
        if cls._instance is None:
            from fakeredis import FakeRedis

            cls._instance = super(FakeTaskClient, cls).__new__(cls)
            cls._redis = FakeRedis()

        return cls._instance

    def __init__(self) -> None:
        super().__init__(default_service="test", redis_client=self._redis)

    def flush(self) -> None:
        self._redis.flushall()

    def pending_job_count(self, queue_name: str) -> int:
        return len(self.queue(queue_name).jobs())

    def drain_pending_jobs(self, queue_name: str) -> None:
        from backend.common.deferred.handlers.defer_handler import run

        jobs = self.queue(queue_name).jobs()
        [run(j.kwargs["data"]) for j in jobs]

    def queue(self, name) -> FakeTaskQueue:
        return FakeTaskQueue(
            name, default_service=self.default_service, redis_client=self._client
        )
