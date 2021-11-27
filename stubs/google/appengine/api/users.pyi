from google.appengine.api import apiproxy_stub_map as apiproxy_stub_map, user_service_pb2 as user_service_pb2
from google.appengine.runtime import apiproxy_errors as apiproxy_errors, context as context
from typing import Any

class Error(Exception): ...
class UserNotFoundError(Error): ...
class RedirectTooLongError(Error): ...
class NotAllowedError(Error): ...

class User:
    def __init__(self, email: Any | None = ..., _auth_domain: Any | None = ..., _user_id: Any | None = ..., federated_identity: Any | None = ..., federated_provider: Any | None = ..., _strict_mode: bool = ...) -> None: ...
    def nickname(self): ...
    def email(self): ...
    def user_id(self): ...
    def auth_domain(self): ...
    def federated_identity(self): ...
    def federated_provider(self): ...
    def __unicode__(self): ...
    def __hash__(self): ...
    def __eq__(self, other): ...
    def __ne__(self, other): ...
    def __lt__(self, other): ...

def create_login_url(dest_url: Any | None = ..., _auth_domain: Any | None = ..., federated_identity: Any | None = ...): ...
CreateLoginURL = create_login_url

def create_logout_url(dest_url, _auth_domain: Any | None = ...): ...
CreateLogoutURL = create_logout_url

def get_current_user(): ...
GetCurrentUser = get_current_user

def is_current_user_admin(): ...
IsCurrentUserAdmin = is_current_user_admin
