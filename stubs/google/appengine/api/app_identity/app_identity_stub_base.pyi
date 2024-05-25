from google.appengine.api import apiproxy_stub as apiproxy_stub, stublib as stublib
from typing import Any

APP_SERVICE_ACCOUNT_NAME: str
APP_DEFAULT_GCS_BUCKET_NAME: str
SIGNING_KEY_NAME: str
N: int
MODULUS_BYTES: int
E: int
D: int
X509_PUBLIC_CERT: str
PREFIX: str
LEN_OF_PREFIX: int
HEADER1: str
HEADER2: str
PADDING: str
LENGTH_OF_SHA256_HASH: int

class AppIdentityServiceStubBase(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    patchers: Any
    def __init__(self, service_name: str = ...) -> None: ...
    def SetDefaultGcsBucketName(self, default_gcs_bucket_name) -> None: ...
    def get_service_account_token(self, scopes, service_account: Any | None = ...): ...
    def get_service_account_name(self): ...
    @staticmethod
    def Create(email_address: Any | None = ..., private_key_path: Any | None = ..., oauth_url: Any | None = ...) -> None: ...
    def Clear(self) -> None: ...
