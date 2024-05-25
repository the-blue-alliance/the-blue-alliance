from google.appengine.api import apiproxy_stub as apiproxy_stub, user_service_pb2 as user_service_pb2
from google.appengine.api.oauth import oauth_api as oauth_api
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from google.appengine.runtime.context import ctx_test_util as ctx_test_util
from typing import Any

class UserServiceStub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    def __init__(self, login_url=..., logout_url=..., service_name: str = ..., auth_domain=..., request_data: Any | None = ...) -> None: ...
    def SetOAuthUser(self, email=..., domain=..., user_id=..., is_admin: bool = ..., scopes: Any | None = ..., client_id=...) -> None: ...
