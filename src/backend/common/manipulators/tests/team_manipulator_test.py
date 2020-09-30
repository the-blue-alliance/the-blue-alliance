import unittest

import pytest

from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
class TestTeamManipulator(unittest.TestCase):
    def setUp(self):
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

    def test_update_tpid(self):
        self.old_team.first_tpid_year = 2016
        self.old_team.first_tpid = 1000

        self.new_team.first_tpid_year = 2017
        self.new_team.first_tpid = 1337

        merged_team = TeamManipulator.updateMerge(self.new_team, self.old_team)
        assert merged_team.first_tpid_year == 2017
        assert merged_team.first_tpid == 1337

    def test_update_tpid_doest_move_backwards(self):
        self.old_team.first_tpid_year = 2016
        self.old_team.first_tpid = 1000

        self.new_team.first_tpid_year = 2015
        self.new_team.first_tpid = 1337

        merged_team = TeamManipulator.updateMerge(self.new_team, self.old_team)
        assert merged_team.first_tpid_year == 2016
        assert merged_team.first_tpid == 1000

    def test_create_lots_of_teams(self):
        number = 500
        teams = [
            Team(id="frc%s" % team_number, team_number=team_number)
            for team_number in range(number)
        ]
        TeamManipulator.createOrUpdate(teams)

        team = Team.get_by_id("frc177")
        self.assertEqual(team.key_name, "frc177")
        self.assertEqual(team.team_number, 177)

        team = Team.get_by_id("frc%s" % (number - 1))
        self.assertEqual(team.key_name, "frc%s" % (number - 1))
        self.assertEqual(team.team_number, number - 1)
