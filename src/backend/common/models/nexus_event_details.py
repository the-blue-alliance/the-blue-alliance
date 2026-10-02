from typing import cast, Set

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import EventKey
from backend.common.nexus_api.types import PitMap


class NexusEventDetails(CachedModel):
    pitmap_json: dict[str, PitMap] = cast(
        dict[str, PitMap],
        ndb.JsonProperty(required=True, indexed=False, compressed=True),
    )
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _mutable_attrs: Set[str] = {
        "pitmap_json",
    }

    def __init__(self, *args, **kw):
        self._affected_references = {
            "key": set(),
        }
        super(NexusEventDetails, self).__init__(*args, **kw)

    @property
    def key_name(self) -> EventKey:
        return str(self.key.id())
