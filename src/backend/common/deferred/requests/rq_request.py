from typing import Dict
from urllib.parse import SplitResult, urlsplit, urlunsplit

from backend.common.deferred.requests.task_request import TaskRequest


_LOCAL_SERVICE_PORTS = {
    "default": 8081,
    "py3-web": 8082,
    "py3-api": 8083,
    "py3-tasks-io": 8084,
}


class RQTaskRequest(TaskRequest):

    service: str

    def __init__(
        self, url: str, headers: Dict[str, str], body: bytes, service: str
    ) -> None:
        self.service = service

        super().__init__(url, headers, body, service)

    @property
    def url(self) -> str:
        url_parts = urlsplit(self._url)

        # Fallback to port 8081, which should be our `default` service on
        port = _LOCAL_SERVICE_PORTS.get(self.service, 8081)

        # Reformat the URL so it's in the format of localhost + relative URL
        local_url_parts = SplitResult(
            scheme="http",
            netloc=f"localhost:{port}",
            path=url_parts.path,
            query=url_parts.query,
            fragment=url_parts.fragment,
        )
        return urlunsplit(local_url_parts)
