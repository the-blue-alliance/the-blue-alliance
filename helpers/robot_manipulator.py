from helpers.manipulator_base import ManipulatorBase


class RobotManipulator(ManipulatorBase):

    @classmethod
    def updateMerge(self, new_robot, old_robot, auto_union=True):
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
