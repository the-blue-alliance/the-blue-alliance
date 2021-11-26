from google.appengine.api.app_identity import app_identity_keybased_stub as app_identity_keybased_stub, app_identity_stub_base as app_identity_stub_base
from google.auth import exceptions as exceptions
from typing import Any

APP_SERVICE_ACCOUNT_NAME: Any

class AppIdentityServiceStub(app_identity_stub_base.AppIdentityServiceStubBase):
    THREADSAFE: bool
    @staticmethod
    def Create(email_address: Any | None = ..., private_key_path: Any | None = ..., oauth_url: Any | None = ...): ...
