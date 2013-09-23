from helpers.manipulator_base import ManipulatorBase


class MediaManipulator(ManipulatorBase):
    """
    Handle Media database writes.
    """

    @classmethod
    def updateMerge(self, new_media, old_media):
        """
        Given an "old" and a "new" Media object, replace the fields in the
        "old" object that are present in the "new" object, but keep fields from
        the "old" object that are null in the "new" object.
        Special case: References (list of Keys) are merged, not overwritten
        """
        attrs = [
            'media_type_enum',
            'media_id',
            'details_json',
            'year',
            'references',
        ]

        for attr in attrs:
            if getattr(new_media, attr) is not None:
                if attr == 'references':
                    combined_references = list(set(getattr(new_media, attr)).union(set(getattr(old_media, attr))))
                    setattr(old_media, attr, combined_references)
                    old_media.dirty = True
                else:
                    if getattr(new_media, attr) != getattr(old_media, attr):
                        setattr(old_media, attr, getattr(new_media, attr))
                        old_media.dirty = True

        return old_media
