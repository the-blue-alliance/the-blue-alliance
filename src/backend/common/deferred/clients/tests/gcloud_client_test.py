from backend.common.deferred.clients.gcloud_client import (
    _DEFAULT_LOCATION,
    GCloudTaskClient,
)
from backend.common.deferred.conftest import FakeCloudTasksClient
from backend.common.deferred.queues.gcloud_queue import GCloudTaskQueue
from backend.common.deferred.requests.gcloud_http_request import (
    GCloudHttpTaskRequestConfiguration,
)


def test_init_default_location(fake_gcloud_client: FakeCloudTasksClient) -> None:
    project = "test"
    client = GCloudTaskClient(project, gcloud_client=FakeCloudTasksClient())
    assert client.project == project
    assert client.location == _DEFAULT_LOCATION
    assert client.http_request_configuration is None


def test_init_location(fake_gcloud_client: FakeCloudTasksClient) -> None:
    project = "test"
    location = "us-zor1"
    client = GCloudTaskClient(
        project, location=location, gcloud_client=FakeCloudTasksClient()
    )
    assert client.project == project
    assert client.location == location
    assert client.http_request_configuration is None


def test_init_http_request_configuration(
    fake_gcloud_client: FakeCloudTasksClient,
) -> None:
    project = "test"
    http_request_configuration = GCloudHttpTaskRequestConfiguration(
        base_url="https://thebluealliance.com"
    )
    client = GCloudTaskClient(
        project,
        http_request_configuration=http_request_configuration,
        gcloud_client=FakeCloudTasksClient(),
    )
    assert client.project == project
    assert client.location == _DEFAULT_LOCATION
    assert client.http_request_configuration == http_request_configuration


def test_queue(fake_gcloud_client: FakeCloudTasksClient) -> None:
    client = GCloudTaskClient("test", gcloud_client=FakeCloudTasksClient())
    queue = client.queue("test_queue")
    assert type(queue) is GCloudTaskQueue
