from backend.common.deferred.clients.rq_client import InlineRQTaskClient, RQTaskClient
from backend.common.redis import RedisClient


class InlineTaskClient(InlineRQTaskClient):
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


# Similar interface to an in-memory RQTaskClient, except with a stubbed out Redis client
class FakeTaskClient(RQTaskClient):
    def __init__(self) -> None:
        from fakeredis import FakeRedis

        super().__init__(default_service="test", redis_client=FakeRedis())
