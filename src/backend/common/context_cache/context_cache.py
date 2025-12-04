from typing import Any

from google.appengine.ext import ndb


CACHE_DATA: dict[str | bytes, Any] = {}


def get[T: (str, bytes)](cache_key: T) -> Any | None:
    full_cache_key = f"{cache_key}:{ndb.get_context.__hash__()}"
    return CACHE_DATA.get(full_cache_key, None)


def set[T: (str, bytes)](cache_key: T, value: Any) -> None:
    full_cache_key = f"{cache_key}:{ndb.get_context.__hash__()}"
    CACHE_DATA[full_cache_key] = value
