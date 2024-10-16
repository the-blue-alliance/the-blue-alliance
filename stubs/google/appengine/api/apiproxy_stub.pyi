from google.appengine.api import apiproxy_rpc as apiproxy_rpc, request_info as request_info
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

MAX_REQUEST_SIZE: Any
REQ_SIZE_EXCEEDS_LIMIT_MSG_TEMPLATE: str

class APIProxyStub:
    THREADSAFE: bool
    request_data: Any
    def __init__(self, service_name, max_request_size=..., request_data: Any | None = ...) -> None: ...
    def CreateRPC(self): ...
    def CheckRequest(self, service, call, request) -> None: ...
    def MakeSyncCall(self, service, call, request, response, request_id: Any | None = ...) -> None: ...
    def SetError(self, error, method: Any | None = ..., error_rate: int = ...) -> None: ...

def Synchronized(method): ...
