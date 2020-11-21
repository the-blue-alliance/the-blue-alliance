from urllib.parse import SplitResult, urlsplit, urlunsplit

from google.cloud.tasks_v2 import AppEngineHttpRequest, AppEngineRouting
from google.cloud.tasks_v2.types import task as gct_task

from backend.common.deferred.requests.gcloud_request import GCloudTaskRequest


class GCloudServiceTaskRequest(GCloudTaskRequest):
    @property
    def url(self) -> str:
        url_parts = urlsplit(self._url)

        # Reformat the URL so it is always a relative URI - aka, drop the `scheme` + `netloc`
        relative_url_parts = SplitResult(
            scheme="",
            netloc="",
            path=url_parts.path,
            query=url_parts.query,
            fragment=url_parts.fragment,
        )
        return urlunsplit(relative_url_parts)

    @property
    def proto_task(self) -> gct_task.Task:
        app_engine_http_request = AppEngineHttpRequest()
        app_engine_http_request.headers = self.headers
        app_engine_http_request.body = self.body
        app_engine_http_request.relative_uri = self.url

        # If no service is specified, GAE will run the task on the default service
        if self.service:
            app_engine_routing = AppEngineRouting()
            app_engine_routing.service = self.service
            app_engine_http_request.app_engine_routing = app_engine_routing

        proto_task = gct_task.Task()
        proto_task.app_engine_http_request = app_engine_http_request

        return proto_task
