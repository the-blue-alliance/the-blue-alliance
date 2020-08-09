from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.media import Media


class MediaManipulator(ManipulatorBase[Media]):
    """
    Handle Media database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_media_cache_keys_and_controllers(affected_refs)
    """

    @classmethod
    def updateMerge(
        cls, new_media: Media, old_media: Media, auto_union: bool = True
    ) -> Media:
        cls._update_attrs(new_media, old_media, auto_union)
        return old_media
