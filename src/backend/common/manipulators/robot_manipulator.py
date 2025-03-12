from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.robot import Robot


class RobotManipulator(ManipulatorBase[Robot]):
    """
    Handle Robot database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.robot_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: Robot,
        old_model: Robot,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> Robot:
        """
        Update and return Robots
        """
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
