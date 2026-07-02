from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import (
    ManipulatorBase,
    TCacheKeyAndQuery,
)
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.insight_v2 import InsightV2


class InsightV2Manipulator(ManipulatorBase[InsightV2]):
    """
    Handle InsightV2 database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[TCacheKeyAndQuery]:
        return get_affected_queries.insight_v2_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: InsightV2,
        old_model: InsightV2,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> InsightV2:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
