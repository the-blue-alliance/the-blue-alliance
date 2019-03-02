import json
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.parsers.first_elasticsearch.first_elasticsearch_team_details_parser import FIRSTElasticSearchTeamDetailsParser
from models.sitevar import Sitevar


class TestFIRSTElasticSearchTeamParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests
        Sitevar(id='website_blacklist', values_json=json.dumps({'websites': ['http://blacklist.com/']})).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_team(self):
        with open('test_data/first_elasticsearch/2015casj_event_teams.json', 'r') as f:
            teams = FIRSTElasticSearchTeamDetailsParser(2015).parse(json.loads(f.read()))

            self.assertEqual(len(teams), 58)

            for team in teams:
                if team.key.id() == 'frc254':
                    self.assertEqual(team.key_name, "frc254")
                    self.assertEqual(team.team_number, 254)
                    self.assertEqual(team.nickname, "The Cheesy Poofs")
                    self.assertEqual(team.rookie_year, 1999)
                    self.assertEqual(team.postalcode, "95126-1215")
                    self.assertEqual(team.website, "http://www.team254.com")
                    self.assertEqual(team.first_tpid, 357159)
                    self.assertEqual(team.first_tpid_year, 2015)

                if team.key.id() == 'frc604':
                    self.assertEqual(team.key_name, "frc604")
                    self.assertEqual(team.team_number, 604)
                    self.assertEqual(team.nickname, "Quixilver")
                    self.assertEqual(team.rookie_year, 2001)
                    self.assertEqual(team.postalcode, "95120")
                    self.assertEqual(team.website, "http://604robotics.com")
                    self.assertEqual(team.first_tpid, 357405)
                    self.assertEqual(team.first_tpid_year, 2015)
                    self.assertEqual(team.motto, "It will work - because it has to.")

                # A team who doesn't have 'http' starting their website
                if team.key.id() == 'frc4990':
                    self.assertEqual(team.key_name, "frc4990")
                    self.assertEqual(team.team_number, 4990)
                    self.assertEqual(team.nickname, "Gryphon Robotics")
                    self.assertEqual(team.rookie_year, 2014)
                    self.assertEqual(team.postalcode, "94010")
                    self.assertEqual(team.website, "http:///gryphonrobotics.org")
                    self.assertEqual(team.first_tpid, 361441)
                    self.assertEqual(team.first_tpid_year, 2015)
                    self.assertEqual(team.motto, None)

                # A team with a blacklisted website
                if team.key.id() == 'frc221':
                    self.assertEqual(team.website, None)
