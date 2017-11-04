from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class RobotManipulator(ManipulatorBase):
    """
    Handle Robot database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_robot_cache_keys_and_controllers(affected_refs)

    @classmethod
    def updateMerge(self, new_robot, old_robot, auto_union=True, attr_whitelist=None):
        """
        Update and return Robots
        """
        immutable_attrs = [
            "team",
            "year",
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "robot_name",
        ]

        for attr in attrs:
            if getattr(new_robot, attr) is not None:
                if getattr(new_robot, attr) != getattr(old_robot, attr):
                    setattr(old_robot, attr, getattr(new_robot, attr))
                    old_robot.dirty = True

        return old_robot
