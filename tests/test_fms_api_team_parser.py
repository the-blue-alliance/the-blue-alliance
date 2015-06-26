import datetime
import json
import unittest2

from datafeeds.parsers.fms_api.fms_api_team_details_parser import FMSAPITeamDetailsParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.district_type import DistrictType
from models.district_team import DistrictTeam
from models.robot import Robot
from models.team import Team


class TestFMSAPITeamParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parseTeamWithDistrict(self):
        with open('test_data/fms_api/2015_frc1124.json', 'r') as f:
            team, districtTeam, robot = FMSAPITeamDetailsParser(2015, "frc1124").parse(json.loads(f.read()))

            # Ensure we get the proper Team model back
            self.assertEqual(team.key_name, "frc1124")
            self.assertEqual(team.team_number, 1124)
            self.assertEqual(team.name, "Avon Public Schools/UTC & AVON HIGH SCHOOL")
            self.assertEqual(team.nickname, "UberBots")
            self.assertEqual(team.address, "Avon, Connecticut, USA")
            self.assertEqual(team.rookie_year, 2003)

            # Test the DistrictTeam model we get back
            self.assertNotEqual(districtTeam, None)
            self.assertEqual(districtTeam.key_name, "2015ne_frc1124")
            self.assertEqual(districtTeam.team.id(), "frc1124")
            self.assertEqual(districtTeam.district, DistrictType.abbrevs['ne'])

            # Test the Robot model we get back
            self.assertNotEqual(robot, None)
            self.assertEqual(robot.key_name, "frc1124_2015")
            self.assertEqual(robot.team.id(), "frc1124")
            self.assertEqual(robot.robot_name, "Orion")

    def test_parseTeamWithNoDistrict(self):
        with open('test_data/fms_api/2015_frc254.json', 'r') as f:
            team, districtTeam, robot = FMSAPITeamDetailsParser(2015, "frc254").parse(json.loads(f.read()))

            # Ensure we get the proper Team model back
            self.assertEqual(team.key_name, "frc254")
            self.assertEqual(team.team_number, 254)
            self.assertEqual(team.name, "NASA Ames Research Center / Google")
            self.assertEqual(team.nickname, "The Cheesy Poofs")
            self.assertEqual(team.address, "San Jose, California, USA")
            self.assertEqual(team.rookie_year, 1999)

            # Test the DistrictTeam model we get back
            self.assertEqual(districtTeam, None)

            # Test the Robot model we get back
            self.assertNotEqual(robot, None)
            self.assertEqual(robot.key_name, "frc254_2015")
            self.assertEqual(robot.team.id(), "frc254")
            self.assertEqual(robot.robot_name, "Deadlift")
