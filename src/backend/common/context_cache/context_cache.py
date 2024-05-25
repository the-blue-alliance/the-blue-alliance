from typing import Any, AnyStr, Dict, Optional, Union

from google.appengine.ext import ndb


CACHE_DATA: Dict[Union[str, bytes], Any] = {}


def get(cache_key: AnyStr) -> Optional[Any]:
    full_cache_key = f"{cache_key}:{ndb.get_context.__hash__()}"
    return CACHE_DATA.get(full_cache_key, None)


def set(cache_key: AnyStr, value: Any) -> None:
    full_cache_key = f"{cache_key}:{ndb.get_context.__hash__()}"
    CACHE_DATA[full_cache_key] = value
