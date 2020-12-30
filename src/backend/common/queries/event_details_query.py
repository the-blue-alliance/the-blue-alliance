from typing import Optional

from backend.common.models.event_details import EventDetails
from backend.common.models.keys import EventKey
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.event_details_converter import (
    EventDetailsConverter,
)
from backend.common.tasklets import typed_tasklet


class EventDetailsQuery(CachedDatabaseQuery[Optional[EventDetails]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "event_details_{event_key}"
    DICT_CONVERTER = EventDetailsConverter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(self, event_key: EventKey) -> Optional[EventDetails]:
        event_details = yield EventDetails.get_by_id_async(event_key)
        return event_details
