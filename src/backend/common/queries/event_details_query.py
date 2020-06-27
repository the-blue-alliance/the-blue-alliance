from typing import Optional

from google.cloud import ndb

from backend.common.futures import TypedFuture
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import EventKey
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.event_details_converter import (
    EventDetailsConverter,
)


class EventDetailsQuery(DatabaseQuery[Optional[EventDetails]]):
    DICT_CONVERTER = EventDetailsConverter

    @ndb.tasklet
    def _query_async(self, event_key: EventKey) -> TypedFuture[Optional[EventDetails]]:
        event_details = yield EventDetails.get_by_id_async(event_key)
        return event_details
