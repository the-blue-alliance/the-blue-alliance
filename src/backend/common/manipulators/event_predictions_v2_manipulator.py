from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.cache_clearing.get_affected_queries import TCacheKeyAndQuery
from backend.common.manipulators.manipulator_base import (
    ManipulatorBase,
)
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.event_predictions_v2 import EventPredictionsV2


class EventPredictionsV2Manipulator(ManipulatorBase[EventPredictionsV2]):
    """
    Handle EventPredictionsV2 database writes and cache invalidation.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[TCacheKeyAndQuery]:
        return get_affected_queries.event_predictions_v2_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: EventPredictionsV2,
        old_model: EventPredictionsV2,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> EventPredictionsV2:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
