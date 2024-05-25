import contextvars
from typing import Any, Dict

PREFIX: str
AUTH_DOMAIN: Any
DEFAULT_VERSION_HOSTNAME: Any
USER_EMAIL: Any
USER_ID: Any
USER_IS_ADMIN: Any
USER_NICKNAME: Any
DEFAULT_NAMESPACE: Any

def init_from_wsgi_environ(wsgi_env) -> Dict[contextvars.ContextVar, contextvars.Token]: ...
