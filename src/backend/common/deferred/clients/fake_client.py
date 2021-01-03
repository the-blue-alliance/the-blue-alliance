from backend.common.deferred.clients.rq_client import RQTaskClient


# Similar interface to an in-memory RQTaskClient, except with a stubbed out Redis client
class FakeTaskClient(RQTaskClient):
    def __init__(self) -> None:
        from fakeredis import FakeRedis

        super().__init__(default_service="test", redis_client=FakeRedis())
