import unittest

import pytest
from google.cloud import ndb

from backend.common.manipulators.robot_manipulator import RobotManipulator
from backend.common.models.robot import Robot
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
class TestRobotManipulator(unittest.TestCase):
    def setUp(self):
        self.old_robot = Robot(
            id="frc177_2012",
            year=2012,
            team=ndb.Key(Team, "frc177"),
            robot_name="First Name",
        )
        self.new_robot = Robot(
            id="frc177_2012",
            year=2012,
            team=ndb.Key(Team, "frc177"),
            robot_name="Second Name",
        )

    def assertMergedRobot(self, robot: Robot) -> None:
        self.assertOldRobot(robot)
        self.assertEqual(robot.robot_name, "Second Name")

    def assertOldRobot(self, robot: Robot) -> None:
        self.assertEqual(robot.year, 2012)
        self.assertEqual(robot.team, ndb.Key(Team, "frc177"))

    def test_createOrUpdate(self) -> None:
        RobotManipulator.createOrUpdate(self.old_robot)
        self.assertOldRobot(Robot.get_by_id("frc177_2012"))
        RobotManipulator.createOrUpdate(self.new_robot)
        self.assertMergedRobot(Robot.get_by_id("frc177_2012"))

    def test_findOrSpawn(self) -> None:
        self.old_robot.put()
        self.assertMergedRobot(RobotManipulator.findOrSpawn(self.new_robot))

    def test_updateMerge(self) -> None:
        self.assertMergedRobot(
            RobotManipulator.updateMerge(self.new_robot, self.old_robot)
        )
