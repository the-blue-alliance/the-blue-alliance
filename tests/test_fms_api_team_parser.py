import json
import unittest2

from datafeeds.parsers.fms_api.fms_api_team_details_parser import FMSAPITeamDetailsParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.district import District
from models.sitevar import Sitevar


class TestFMSAPITeamParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests
        Sitevar(id='website_blacklist', values_json=json.dumps({'websites': ['http://blacklist.com/']})).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_team_with_district(self):
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
            self.assertEqual(districtTeam.district_key, ndb.Key(District, '2015ne'))

            # Test the Robot model we get back
            self.assertNotEqual(robot, None)
            self.assertEqual(robot.key_name, "frc1124_2015")
            self.assertEqual(robot.team.id(), "frc1124")
            self.assertEqual(robot.robot_name, "Orion")

    def test_parse_team_with_no_district(self):
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

    def test_parse_team_websites(self):
        # Modify the websites to some known bad ones, and ensure the parser can recover
        bad_websites = [None, '', 'www.firstinspires.org', 'website.com', 'www.website.com', 'http://website.com',
                        'https://website.com', 'ftp://website.com', 'http://blacklist.com/']
        expected_sites = [None, None, None, 'http://website.com', 'http://www.website.com', 'http://website.com',
                          'https://website.com', None, '']
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

    def test_parse_2017_team(self):
        with open('test_data/fms_api/2017_frc604.json', 'r') as f:
            models, more_pages = FMSAPITeamDetailsParser(2017).parse(json.loads(f.read()))

            self.assertFalse(more_pages)
            self.assertEqual(len(models), 1)

            team, districtTeam, robot = models[0]

            # Ensure we get the proper Team model back
            self.assertEqual(team.key_name, "frc604")
            self.assertEqual(team.team_number, 604)
            self.assertEqual(team.name, "IBM/Team Grandma/The Brin Wojcicki Foundation/BAE Systems/Boston Scientific - The Argosy Foundation/Qualcomm/Intuitive Surgical/Leland Bridge/Councilman J. Khamis/Almaden Valley Women's Club/NVIDIA/Hurricane Electric/Exatron/MDR Precision/SOLIDWORKS/Hurricane Electric/Dropbox/GitHub&Leland High")
            self.assertEqual(team.nickname, "Quixilver")
            self.assertEqual(team.city, "San Jose")
            self.assertEqual(team.state_prov, "California")
            self.assertEqual(team.country, "USA")
            self.assertEqual(team.rookie_year, 2001)
            self.assertEqual(team.website, "http://604Robotics.com")

            # Test the DistrictTeam model we get back
            self.assertEqual(districtTeam, None)

            # Test the Robot model we get back
            self.assertNotEqual(robot, None)
            self.assertEqual(robot.key_name, "frc604_2017")
            self.assertEqual(robot.team.id(), "frc604")
            self.assertEqual(robot.robot_name, "Ratchet")

            # New properties for 2017
            self.assertEqual(team.school_name, "Leland High")
            self.assertEqual(team.home_cmp, "cmptx")
