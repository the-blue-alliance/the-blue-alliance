from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.insight import Insight


class InsightManipulator(ManipulatorBase[Insight]):
    """
    Handle Insight database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.insight_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls, new_model: Insight, old_model: Insight, auto_union: bool = True
    ) -> Insight:
        """
        Given an "old" and a "new" Insight object, replace the fields in the
        "old" Insight that are present in the "new" Insight, but keep fields from
        the "old" Insight that are null in the "new" insight.
        """
        cls._update_attrs(new_model, old_model, auto_union)
        return old_model
