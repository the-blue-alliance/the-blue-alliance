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
        cls, new_robot: Robot, old_robot: Robot, auto_union: bool = True
    ) -> Robot:
        """
        Update and return Robots
        """
        cls._update_attrs(new_robot, old_robot, auto_union)
        return old_robot
