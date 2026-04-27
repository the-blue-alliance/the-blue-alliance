from typing import Any, cast, Set

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import EventKey


class NexusPitMap(CachedModel):
    data_json: dict[str, Any] = cast(
        dict[str, Any],
        ndb.JsonProperty(required=True, indexed=False, compressed=True),
    )
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _mutable_attrs: Set[str] = {
        "data_json",
    }

    def __init__(self, *args, **kw):
        self._affected_references = {
            "key": set(),
        }
        super(NexusPitMap, self).__init__(*args, **kw)

    @property
    def key_name(self) -> EventKey:
        return str(self.key.id())
