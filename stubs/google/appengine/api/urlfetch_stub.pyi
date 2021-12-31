from google.appengine.api import apiproxy_stub as apiproxy_stub, full_app_id as full_app_id, urlfetch as urlfetch, urlfetch_service_pb2 as urlfetch_service_pb2
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

MAX_REQUEST_SIZE: Any
MAX_RESPONSE_SIZE: Any
MAX_REDIRECTS: Any
REDIRECT_STATUSES: Any
PRESERVE_ON_REDIRECT: Any

def GetHeaders(msg, key): ...

class URLFetchServiceStub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    http_proxy: Any
    def __init__(self, service_name: str = ..., urlmatchers_to_fetch_functions: Any | None = ...) -> None: ...
