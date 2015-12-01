import json
import unittest2

from google.appengine.ext import testbed

from datafeeds.parsers.first_elasticsearch.first_elasticsearch_team_details_parser import FIRSTElasticSearchTeamDetailsParser


class TestFIRSTElasticSearchTeamParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parseTeam(self):
        with open('test_data/first_elasticsearch/2015casj_event_teams.json', 'r') as f:
            teams = FIRSTElasticSearchTeamDetailsParser(2015).parse(json.loads(f.read()))

            self.assertEqual(len(teams), 58)

            for team in teams:
                if team.key.id() == 'frc254':
                    self.assertEqual(team.key_name, "frc254")
                    self.assertEqual(team.team_number, 254)
                    self.assertEqual(team.nickname, "The Cheesy Poofs")
                    self.assertEqual(team.address, "San Jose, CA, USA")
                    self.assertEqual(team.rookie_year, 1999)
                    self.assertEqual(team.website, "http://www.team254.com")
                    self.assertEqual(team.first_tpid, 357159)
                    self.assertEqual(team.first_tpid_year, 2015)
