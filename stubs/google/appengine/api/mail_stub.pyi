from google.appengine.api import apiproxy_stub as apiproxy_stub, mail as mail, mail_service_pb2 as mail_service_pb2
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

MAX_REQUEST_SIZE: Any
JAVA_TO_PYTHON_LOG_LEVELS: Any

class MailServiceStub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    def __init__(self, host: Any | None = ..., port: int = ..., user: str = ..., password: str = ..., enable_sendmail: bool = ..., show_mail_body: bool = ..., service_name: str = ..., allow_tls: bool = ...) -> None: ...
    def get_sent_messages(self, to: Any | None = ..., sender: Any | None = ..., subject: Any | None = ..., body: Any | None = ..., html: Any | None = ..., amp_html: Any | None = ...): ...
    def Clear(self) -> None: ...
