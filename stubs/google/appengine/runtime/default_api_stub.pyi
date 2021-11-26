import threading
from google.appengine.api import apiproxy_rpc as apiproxy_rpc, apiproxy_stub_map as apiproxy_stub_map
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

TICKET_HEADER: str
DEV_TICKET_HEADER: str
DAPPER_ENV_KEY: str
SERVICE_BRIDGE_HOST: str
API_PORT: int
SERVICE_ENDPOINT_NAME: str
APIHOST_METHOD: str
PROXY_PATH: str
DAPPER_HEADER: str
SERVICE_DEADLINE_HEADER: str
SERVICE_ENDPOINT_HEADER: str
SERVICE_METHOD_HEADER: str
RPC_CONTENT_TYPE: str
DEFAULT_TIMEOUT: int
DEADLINE_DELTA_SECONDS: int
MAX_CONCURRENT_API_CALLS: int
URLLIB3_POOL_COUNT: int
URLLIB3_POOL_SIZE: int

class DefaultApiRPC(apiproxy_rpc.RPC): ...

class _UseRequestSecurityTicketLocal(threading.local):
    use_ticket_header_value: bool
    def __init__(self) -> None: ...

class DefaultApiStub:
    @classmethod
    def SetUseRequestSecurityTicketForThread(cls, value) -> None: ...
    @classmethod
    def ShouldUseRequestSecurityTicketForThread(cls): ...
    thread_pool: Any
    http: Any
    def __init__(self) -> None: ...
    def MakeSyncCall(self, service, call, request, response) -> None: ...
    def CreateRPC(self): ...

def Register(stub) -> None: ...
