from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class MediaManipulator(ManipulatorBase):
    """
    Handle Media database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_media_cache_keys_and_controllers(affected_refs)

    @classmethod
    def updateMerge(self, new_media, old_media, auto_union=True):
        """
        Given an "old" and a "new" Media object, replace the fields in the
        "old" object that are present in the "new" object, but keep fields from
        the "old" object that are null in the "new" object.
        Special case: References (list of Keys) are merged, not overwritten
        """
        attrs = [
            'media_type_enum',
            'foreign_key',
            'details_json',
            'year',
        ]

        list_attrs = []

        auto_union_attrs = [
            'references',
            'preferred_references',
            'media_tag_enum',
        ]

        old_media._updated_attrs = []

        # if not auto_union, treat auto_union_attrs as list_attrs
        if not auto_union:
            list_attrs += auto_union_attrs
            auto_union_attrs = []

        for attr in attrs:
            if getattr(new_media, attr) is not None:
                if getattr(new_media, attr) != getattr(old_media, attr):
                    setattr(old_media, attr, getattr(new_media, attr))
                    old_media._updated_attrs.append(attr)
                    old_media.dirty = True

        for attr in list_attrs:
            if len(getattr(new_media, attr)) > 0 or not auto_union:
                if getattr(new_media, attr) != getattr(old_media, attr):
                    setattr(old_media, attr, getattr(new_media, attr))
                    old_media._updated_attrs.append(attr)
                    old_media.dirty = True

        for attr in auto_union_attrs:
            old_set = set(getattr(old_media, attr))
            new_set = set(getattr(new_media, attr))
            unioned = old_set.union(new_set)
            if unioned != old_set:
                setattr(old_media, attr, list(unioned))
                old_media._updated_attrs.append(attr)
                old_media.dirty = True

        return old_media
