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
            models, more_pages = FMSAPITeamDetailsParser(2015).parse(json.loads(f.read()))

            self.assertFalse(more_pages)
            self.assertEqual(len(models), 1)

            team, districtTeam, robot = models[0]

            # Ensure we get the proper Team model back
            self.assertEqual(team.key_name, "frc1124")
            self.assertEqual(team.team_number, 1124)
            self.assertEqual(team.name, "Avon Public Schools/UTC & AVON HIGH SCHOOL")
            self.assertEqual(team.nickname, "UberBots")
            self.assertEqual(team.city, "Avon")
            self.assertEqual(team.state_prov, "Connecticut")
            self.assertEqual(team.country, "USA")
            self.assertEqual(team.rookie_year, 2003)
            self.assertEqual(team.website, "http://uberbots.org")

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
            models, more_pages = FMSAPITeamDetailsParser(2015).parse(json.loads(f.read()))

            self.assertFalse(more_pages)
            self.assertEqual(len(models), 1)

            team, districtTeam, robot = models[0]

            # Ensure we get the proper Team model back
            self.assertEqual(team.key_name, "frc254")
            self.assertEqual(team.team_number, 254)
            self.assertEqual(team.name, "NASA Ames Research Center / Google")
            self.assertEqual(team.nickname, "The Cheesy Poofs")
            self.assertEqual(team.city, "San Jose")
            self.assertEqual(team.state_prov, "California")
            self.assertEqual(team.country, "USA")
            self.assertEqual(team.rookie_year, 1999)
            self.assertEqual(team.website, "http://team254.com/")

            # Test the DistrictTeam model we get back
            self.assertEqual(districtTeam, None)

            # Test the Robot model we get back
            self.assertNotEqual(robot, None)
            self.assertEqual(robot.key_name, "frc254_2015")
            self.assertEqual(robot.team.id(), "frc254")
            self.assertEqual(robot.robot_name, "Deadlift")

    def test_parseTeamWebsites(self):
        # Modify the websites to some known bad ones, and ensure the parser can recover
        bad_websites = [None, '', 'www.firstinspires.org', 'website.com', 'www.website.com', 'http://website.com',
                        'https://website.com', 'ftp://website.com']
        expected_sites = [None, None, None, 'http:///website.com', 'http:///www.website.com', 'http://website.com',
                          'https://website.com', 'ftp://website.com']
        # When urllib prepends the scheme, it'll add three slashes because of how its parsed.
        # Browsers won't care about the extra /, so it shouldn't be an issue
        # http://stackoverflow.com/questions/7289481/urlparse-urlparse-returning-3-instead-of-2-after-scheme
        with open('test_data/fms_api/2015_frc1124.json', 'r') as f:
            team_data = json.loads(f.read())
            for site, expected in zip(bad_websites, expected_sites):
                team_data['teams'][0]['website'] = site
                models, more_pages = FMSAPITeamDetailsParser(2015).parse(team_data)

                self.assertFalse(more_pages)
                self.assertEqual(len(models), 1)

                team, districtTeam, robot = models[0]

                # Ensure we get the proper Team model back
                self.assertEqual(team.key_name, "frc1124")
                self.assertEqual(team.team_number, 1124)
                self.assertEqual(team.name, "Avon Public Schools/UTC & AVON HIGH SCHOOL")
                self.assertEqual(team.nickname, "UberBots")
                self.assertEqual(team.city, "Avon")
                self.assertEqual(team.state_prov, "Connecticut")
                self.assertEqual(team.country, "USA")
                self.assertEqual(team.rookie_year, 2003)
                self.assertEqual(team.website, expected)
