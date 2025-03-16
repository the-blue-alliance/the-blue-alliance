from datetime import timedelta

from backend.common.memcache_models.memcache_model import MemcacheModel
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.keys import EventKey


class EventNexusQueueStatusMemcache(MemcacheModel[EventQueueStatus]):

    def __init__(self, event_key: EventKey) -> None:
        super().__init__()
        self.event_key = event_key

    def key(self) -> bytes:
        return f"nexus_queue_status_{self.event_key}".encode()

    def ttl(self) -> timedelta:
        return timedelta(minutes=5)
