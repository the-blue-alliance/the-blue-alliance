from typing import Optional

from google.cloud import tasks_v2

from backend.common.deferred.clients.task_client import TaskClient
from backend.common.deferred.queues.gcloud_queue import GCloudTaskQueue
from backend.common.deferred.requests.gcloud_http_request import (
    GCloudHttpTaskRequestConfiguration,
)


_DEFAULT_LOCATION = "us-central1"


class GCloudTaskClient(TaskClient[GCloudTaskQueue]):

    project: str
    location: str
    http_request_configuration: Optional[GCloudHttpTaskRequestConfiguration]

    def __init__(
        self,
        project: str,
        *,
        location: Optional[str] = None,
        http_request_configuration: Optional[GCloudHttpTaskRequestConfiguration] = None,
        gcloud_client: Optional[tasks_v2.CloudTasksClient] = None
    ) -> None:
        self.project = project
        self.location = location if location else _DEFAULT_LOCATION
        self.http_request_configuration = http_request_configuration

        gcloud_client = gcloud_client if gcloud_client else tasks_v2.CloudTasksClient()
        super().__init__(gcloud_client)

    def queue(self, name) -> GCloudTaskQueue:
        queue_path = self._client.queue_path(self.project, self.location, name)

        return GCloudTaskQueue(
            queue_path,
            http_request_configuration=self.http_request_configuration,
            gcloud_client=self._client,
        )
