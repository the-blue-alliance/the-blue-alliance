from fakeredis import FakeRedis

from backend.common.deferred.clients.rq_client import RQTaskClient
from backend.common.deferred.queues.rq_queue import RQTaskQueue


def test_init(fake_redis_client: FakeRedis) -> None:
    default_service = "default"
    client = RQTaskClient(
        default_service=default_service, redis_client=fake_redis_client
    )
    assert client.default_service == default_service


def test_queue(fake_redis_client: FakeRedis) -> None:
    client = RQTaskClient(default_service="default", redis_client=fake_redis_client)
    queue = client.queue("test_queue")
    assert type(queue) == RQTaskQueue
