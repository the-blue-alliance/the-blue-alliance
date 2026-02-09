import json
from typing import Generic, Mapping, Optional, TypeVar

from google.appengine.api import urlfetch_service_pb2
from google.appengine.api.urlfetch import _URLFetchResult
from pyre_extensions import JSON

from backend.common.consts.string_enum import StrEnum


class URLFetchMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


T = TypeVar("T")


class TypedURLFetchResult(Generic[T]):
    """
    A URLFetchResult with a typed JSON response.
    """

    request_url: str

    content: str
    status_code: int
    content_was_truncated: bool
    header_msg: str
    headers: Mapping[str, str]

    # If a redirect was followed, the ultimate URL
    final_url: Optional[str]

    def __init__(self, url: str, res: _URLFetchResult, json_type: type[T]) -> None:
        self.request_url = url
        self.content = res.content
        self.status_code = res.status_code
        self.content_was_truncated = res.content_was_truncated
        self.final_url = res.final_url
        self.header_msg = res.header_msg
        self.headers = res.headers
        self._json_type = json_type

    @property
    def url(self) -> str:
        return self.final_url or self.request_url

    def json(self) -> T | None:
        if not self.content:
            return None
        return json.loads(self.content)

    @classmethod
    def typed_mock_for_content(
        cls, url: str, status_code: int, content: str, json_type: type[T]
    ) -> "TypedURLFetchResult[T]":
        response_proto = cls.mock_urlfetch_result(url, status_code, content)
        return cls(url, response_proto, json_type)

    @classmethod
    def mock_urlfetch_result(
        cls, url: str, status_code: int, content: str
    ) -> _URLFetchResult:
        """Create a mock _URLFetchResult for testing urlfetch calls."""
        response_proto = urlfetch_service_pb2.URLFetchResponse()
        response_proto.Content = content.encode()
        response_proto.StatusCode = status_code
        return _URLFetchResult(response_proto)


class URLFetchResult(TypedURLFetchResult[JSON]):

    def __init__(self, url: str, res: _URLFetchResult) -> None:
        super().__init__(url, res, JSON)

    @classmethod
    def mock_for_content(
        cls, url: str, status_code: int, content: str
    ) -> "URLFetchResult":
        response_proto = cls.mock_urlfetch_result(url, status_code, content)
        return cls(url, response_proto)
