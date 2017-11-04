from helpers.manipulator_base import ManipulatorBase


class InsightManipulator(ManipulatorBase):
    """
    Handle Insight database writes.
    """

    @classmethod
    def updateMerge(self, new_insight, old_insight, auto_union=True, attr_whitelist=None):
        """
        Given an "old" and a "new" Insight object, replace the fields in the
        "old" Insight that are present in the "new" Insight, but keep fields from
        the "old" Insight that are null in the "new" insight.
        """
        attrs = [
            'name',
            'year',
            'data_json',
        ]

        for attr in attrs:
            if getattr(new_insight, attr) is not None:
                if getattr(new_insight, attr) != getattr(old_insight, attr):
                    setattr(old_insight, attr, getattr(new_insight, attr))
                    old_insight.dirty = True
            if getattr(new_insight, attr) == "None":
                if getattr(old_insight, attr, None) != None:
                    setattr(old_insight, attr, None)
                    old_insight.dirty = True

        return old_insight
