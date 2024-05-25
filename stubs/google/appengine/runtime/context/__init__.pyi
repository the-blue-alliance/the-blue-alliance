import contextvars
from google.appengine.runtime.context import gae_headers as gae_headers, wsgi as wsgi
from typing import Any, Dict

READ_FROM_OS_ENVIRON: Any

def get(key, default: Any | None = ...): ...
def init_from_wsgi_environ(wsgi_env) -> Dict[contextvars.ContextVar, contextvars.Token]: ...
