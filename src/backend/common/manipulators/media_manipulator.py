from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.media import Media


class MediaManipulator(ManipulatorBase[Media]):
    """
    Handle Media database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.media_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: Media,
        old_model: Media,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> Media:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
