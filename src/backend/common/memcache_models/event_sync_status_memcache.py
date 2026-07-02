import datetime
from datetime import timedelta
from typing import Dict, Optional, TypedDict

from backend.common.memcache_models.memcache_model import MemcacheModel
from backend.common.models.keys import EventKey


class SyncEndpointStatus(TypedDict):
    last_success_time: Optional[str]
    num_consecutive_failures: int


EventSyncStatus = Dict[str, SyncEndpointStatus]


class EventSyncStatusMemcache(MemcacheModel[EventSyncStatus]):
    def __init__(self, event_key: EventKey) -> None:
        super().__init__()
        self.event_key = event_key

    def key(self) -> bytes:
        return f"event_sync_status_{self.event_key}".encode()

    def ttl(self) -> timedelta:
        return timedelta(days=30)

    def record_success(
        self, endpoint: str, now: Optional[datetime.datetime] = None
    ) -> bool:
        status = self.get() or {}
        utc_timezone = datetime.timezone(datetime.timedelta(0))
        last_success_time = (now or datetime.datetime.now(utc_timezone)).isoformat()

        status[endpoint] = {
            "last_success_time": last_success_time,
            "num_consecutive_failures": 0,
        }
        return self.put(status)

    def record_failure(self, endpoint: str) -> bool:
        status = self.get() or {}
        endpoint_status = status.get(
            endpoint,
            {
                "last_success_time": None,
                "num_consecutive_failures": 0,
            },
        )

        status[endpoint] = {
            "last_success_time": endpoint_status["last_success_time"],
            "num_consecutive_failures": endpoint_status["num_consecutive_failures"] + 1,
        }
        return self.put(status)
