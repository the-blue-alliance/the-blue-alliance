from typing import List

from backend.common.cache_clearing.get_affected_queries import TCacheKeyAndQuery
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.nexus_event_details import NexusEventDetails


class NexusEventDetailsManipulator(ManipulatorBase[NexusEventDetails]):
    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[TCacheKeyAndQuery]:
        return []

    @classmethod
    def updateMerge(
        cls,
        new_model: NexusEventDetails,
        old_model: NexusEventDetails,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> NexusEventDetails:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
