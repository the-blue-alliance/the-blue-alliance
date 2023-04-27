from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.insight import Insight


class InsightManipulator(ManipulatorBase[Insight]):
    """
    Handle Insight database writes.
    """

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
