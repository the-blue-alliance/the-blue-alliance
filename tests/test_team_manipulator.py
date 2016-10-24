import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.team_manipulator import TeamManipulator
from models.team import Team


class TestTeamManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.old_team = Team(
            id="frc177",
            team_number=177,
            rookie_year=1996,
            first_tpid=61771,
            first_tpid_year=2012,
        )

        self.new_team = Team(
            id="frc177",
            team_number=177,
            rookie_year=1995,
            website="http://www.bobcatrobotics.org",
        )

    def tearDown(self):
        self.testbed.deactivate()

    def assertMergedTeam(self, team):
        self.assertOldTeam(team)
        self.assertEqual(team.website, "http://www.bobcatrobotics.org")
        self.assertEqual(team.rookie_year, 1995)

    def assertOldTeam(self, team):
        self.assertEqual(team.first_tpid, 61771)
        self.assertEqual(team.first_tpid_year, 2012)
        self.assertEqual(team.key_name, "frc177")
        self.assertEqual(team.team_number, 177)

    def test_createOrUpdate(self):
        TeamManipulator.createOrUpdate(self.old_team)
        self.assertOldTeam(Team.get_by_id("frc177"))
        TeamManipulator.createOrUpdate(self.new_team)
        self.assertMergedTeam(Team.get_by_id("frc177"))

    def test_findOrSpawn(self):
        self.old_team.put()
        self.assertMergedTeam(TeamManipulator.findOrSpawn(self.new_team))

    def test_updateMerge(self):
        self.assertMergedTeam(TeamManipulator.updateMerge(self.new_team, self.old_team))

    def test_create_lots_of_teams(self):
        number = 500
        teams = [Team(
            id="frc%s" % team_number,
            team_number=team_number)
            for team_number in range(number)]
        TeamManipulator.createOrUpdate(teams)

        team = Team.get_by_id("frc177")
        self.assertEqual(team.key_name, "frc177")
        self.assertEqual(team.team_number, 177)

        team = Team.get_by_id("frc%s" % (number - 1))
        self.assertEqual(team.key_name, "frc%s" % (number - 1))
        self.assertEqual(team.team_number, number - 1)
