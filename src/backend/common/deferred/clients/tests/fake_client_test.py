from fakeredis import FakeRedis

from backend.common.deferred.clients.fake_client import FakeTaskClient


def test_init() -> None:
    client = FakeTaskClient()
    assert client.default_service == "test"
    assert type(client._client) is FakeRedis
