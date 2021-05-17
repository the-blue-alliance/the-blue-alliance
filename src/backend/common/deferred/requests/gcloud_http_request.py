from dataclasses import dataclass
from typing import Dict
from urllib.parse import SplitResult, urlsplit, urlunsplit

from google.cloud.tasks_v2 import HttpRequest
from google.cloud.tasks_v2.types import task as gct_task

from backend.common.deferred.requests.gcloud_request import GCloudTaskRequest


@dataclass
class GCloudHttpTaskRequestConfiguration:
    base_url: str


class GCloudHttpTaskRequest(GCloudTaskRequest):

    configuration: GCloudHttpTaskRequestConfiguration

    def __init__(
        self,
        configuration: GCloudHttpTaskRequestConfiguration,
        url: str,
        headers: Dict[str, str],
        body: bytes,
    ) -> None:
        self.configuration = configuration

        super().__init__(url, headers, body)

    @property
    def url(self) -> str:
        base_url_parts = urlsplit(self.configuration.base_url)
        url_parts = urlsplit(self._url)

        # Reformat the URL so it's in the format of base url + relative URL
        remote_url_parts = SplitResult(
            scheme=base_url_parts.scheme,
            netloc=base_url_parts.netloc,
            path=url_parts.path,
            query=url_parts.query,
            fragment=url_parts.fragment,
        )
        return urlunsplit(remote_url_parts)

    @property
    def proto_task(self) -> gct_task.Task:
        http_request = HttpRequest()
        http_request.headers = self.headers
        http_request.body = self.body
        http_request.url = self.url

        proto_task = gct_task.Task()
        proto_task.http_request = http_request

        return proto_task
