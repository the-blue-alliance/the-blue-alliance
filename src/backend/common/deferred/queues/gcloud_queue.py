from typing import Dict, Optional

from google.cloud import tasks_v2

from backend.common.deferred.queues.task_queue import TaskQueue
from backend.common.deferred.requests.gcloud_http_request import (
    GCloudHttpTaskRequestConfiguration,
)
from backend.common.deferred.requests.gcloud_request import GCloudTaskRequest


class GCloudTaskQueue(TaskQueue[GCloudTaskRequest]):

    http_request_configuration: Optional[GCloudHttpTaskRequestConfiguration]

    def __init__(
        self,
        name: str,
        *,
        http_request_configuration: Optional[GCloudHttpTaskRequestConfiguration] = None,
        gcloud_client: tasks_v2.CloudTasksClient
    ) -> None:
        self.http_request_configuration = http_request_configuration
        self._gcloud_client = gcloud_client

        super().__init__(name)

    def _task_request(
        self,
        url: str,
        headers: Dict[str, str],
        body: bytes,
        service: Optional[str] = None,
    ) -> GCloudTaskRequest:
        http_request_configuration = self.http_request_configuration
        if http_request_configuration is not None:
            from backend.common.deferred.requests.gcloud_http_request import (
                GCloudHttpTaskRequest,
            )

            return GCloudHttpTaskRequest(http_request_configuration, url, headers, body)
        else:
            from backend.common.deferred.requests.gcloud_service_request import (
                GCloudServiceTaskRequest,
            )

            return GCloudServiceTaskRequest(url, headers, body, service)

    def _enqueue(self, request: GCloudTaskRequest) -> None:
        proto_request = tasks_v2.CreateTaskRequest()
        proto_request.parent = self.name
        proto_request.task = request.proto_task

        self._gcloud_client.create_task(request=proto_request)
