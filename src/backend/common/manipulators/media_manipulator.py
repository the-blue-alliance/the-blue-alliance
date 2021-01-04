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
        cls, new_media: Media, old_media: Media, auto_union: bool = True
    ) -> Media:
        cls._update_attrs(new_media, old_media, auto_union)
        return old_media
