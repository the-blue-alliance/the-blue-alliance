from google.appengine.api import apiproxy_stub as apiproxy_stub, request_info as request_info
from google.appengine.api.system import system_service_pb2 as system_service_pb2
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

class SystemServiceStub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    default_cpu: Any
    default_memory: Any
    num_calls: Any
    def __init__(self, default_cpu: Any | None = ..., default_memory: Any | None = ..., request_data: Any | None = ...) -> None: ...
    def set_backend_info(self, backend_info) -> None: ...
    def get_backend_info(self): ...
