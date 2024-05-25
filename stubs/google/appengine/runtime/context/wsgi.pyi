import contextvars
from typing import Any, Dict

HTTP_HOST: Any
HTTP_USER_AGENT: Any
HTTP_X_CLOUD_TRACE_CONTEXT: Any
PATH_INFO: Any
PATH_TRANSLATED: Any
QUERY_STRING: Any
SERVER_NAME: Any
SERVER_PORT: Any
SERVER_PROTOCOL: Any

def init_from_wsgi_environ(wsgi_env) -> Dict[contextvars.ContextVar, contextvars.Token]: ...
