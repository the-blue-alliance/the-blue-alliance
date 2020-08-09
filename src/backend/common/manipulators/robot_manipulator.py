from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.robot import Robot


class RobotManipulator(ManipulatorBase[Robot]):
    """
    Handle Robot database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_robot_cache_keys_and_controllers(affected_refs)
    """

    @classmethod
    def updateMerge(
        cls, new_robot: Robot, old_robot: Robot, auto_union: bool = True
    ) -> Robot:
        """
        Update and return Robots
        """
        cls._update_attrs(new_robot, old_robot, auto_union)
        return old_robot
