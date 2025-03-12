import json
from typing import Mapping, Optional

from google.appengine.api import urlfetch_service_pb2
from google.appengine.api.urlfetch import _URLFetchResult
from pyre_extensions import JSON


class URLFetchResult:
    """
    A strongly typed abstraction of GAE's URLFetchResult
    """

    request_url: str

    content: str
    status_code: int
    content_was_truncated: bool
    header_msg: str
    headers: Mapping[str, str]

    # If a redirect was followed, the ultimate URL
    final_url: Optional[str]

    def __init__(self, url: str, res: _URLFetchResult) -> None:
        self.request_url = url
        self.content = res.content
        self.status_code = res.status_code
        self.content_was_truncated = res.content_was_truncated
        self.final_url = res.final_url
        self.header_msg = res.header_msg
        self.headers = res.headers

    @property
    def url(self) -> str:
        return self.final_url or self.request_url

    def json(self) -> Optional[JSON]:
        if not self.content:
            return None
        return json.loads(self.content)

    @classmethod
    def mock_for_content(
        cls, url: str, status_code: int, content: str
    ) -> "URLFetchResult":
        response_proto = urlfetch_service_pb2.URLFetchResponse()
        response_proto.Content = content.encode()
        response_proto.StatusCode = status_code
        return cls(url, _URLFetchResult(response_proto))
