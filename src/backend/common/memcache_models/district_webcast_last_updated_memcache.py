from datetime import timedelta
from typing import Dict, TypedDict

from backend.common.memcache_models.memcache_model import MemcacheModel
from backend.common.models.keys import DistrictKey


class DistrictWebcastLastUpdatedData(TypedDict):
    district_last_updated: Dict[DistrictKey, int]


class DistrictWebcastLastUpdatedMemcache(MemcacheModel[DistrictWebcastLastUpdatedData]):
    def key(self) -> bytes:
        return b"district_webcast_last_updated"

    def ttl(self) -> timedelta:
        # Long enough to span multiple cron runs while still naturally expiring.
        return timedelta(days=7)
