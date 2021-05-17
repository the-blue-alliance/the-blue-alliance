import pytest

from fakeredis import FakeRedis
from google.cloud import tasks_v2


class FakeCloudTasksClient(tasks_v2.CloudTasksClient):
    def __init__(self):
        pass


@pytest.fixture
def fake_gcloud_client() -> FakeCloudTasksClient:
    return FakeCloudTasksClient()


@pytest.fixture
def fake_redis_client() -> FakeRedis:
    return FakeRedis()
