from typing import Any, Generator, Optional

from backend.common.models.event_predictions_v2 import EventPredictionsV2
from backend.common.models.keys import EventKey
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.event_predictions_v2_converter import (
    EventPredictionsV2Converter,
    EventPredictionsV2Dict,
)
from backend.common.tasklets import typed_tasklet


class EventPredictionsV2Query(
    CachedDatabaseQuery[Optional[EventPredictionsV2], Optional[EventPredictionsV2Dict]]
):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "event_predictions_v2_{event_key}"
    MODEL_CACHING_ENABLED = False  # No need to cache a point query
    DICT_CONVERTER = EventPredictionsV2Converter

    def __init__(self, event_key: EventKey) -> None:
        super().__init__(event_key=event_key)

    @typed_tasklet
    def _query_async(
        self, event_key: EventKey
    ) -> Generator[Any, Any, Optional[EventPredictionsV2]]:
        event_predictions = yield EventPredictionsV2.get_by_id_async(event_key)
        return event_predictions
