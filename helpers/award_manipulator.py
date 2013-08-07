from helpers.manipulator_base import ManipulatorBase


class AwardManipulator(ManipulatorBase):
    """
    Handle Award database writes.
    """

    @classmethod
    def updateMerge(self, new_award, old_award):
        """
        Given an "old" and a "new" Award object, replace the fields in the
        "old" award that are present in the "new" award, but keep fields from
        the "old" award that are null in the "new" award.
        """
        attrs = [
            'name',
            'official_name',
            'year',
            'team',
            'awardee',
            'event',
        ]

        list_attrs = []

        for attr in attrs:
            if getattr(new_award, attr) is not None:
                if getattr(new_award, attr) != getattr(old_award, attr):
                    setattr(old_award, attr, getattr(new_award, attr))
                    old_award.dirty = True
            if getattr(new_award, attr) == "None":
                if getattr(old_award, attr, None) != None:
                    setattr(old_award, attr, None)
                    old_award.dirty = True

        for attr in list_attrs:
            if len(getattr(new_award, attr)) > 0:
                if getattr(new_award, attr) != getattr(old_award, attr):
                    setattr(old_award, attr, getattr(new_award, attr))
                    old_award.dirty = True

        return old_award
