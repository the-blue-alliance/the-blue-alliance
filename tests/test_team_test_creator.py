import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.team.team_test_creator import TeamTestCreator
from models.team import Team


class TestEventTeamCreator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.teams = []

    def tearDown(self):
        for team in self.teams:
            team.key.delete()

        self.testbed.deactivate()

    def test_creates(self):
        self.teams.extend(TeamTestCreator.createSixTeams())

        teams = Team.query().order(Team.team_number).fetch(60)
        self.assertEqual(len(teams), 6)
