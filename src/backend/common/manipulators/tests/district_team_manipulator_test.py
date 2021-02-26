import unittest

import pytest
from google.cloud import ndb

from backend.common.manipulators.district_team_manipulator import (
    DistrictTeamManipulator,
)
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
class TestDistrictManipulator(unittest.TestCase):
    def setUp(self):
        self.old_district_team = DistrictTeam(
            id="2015ne_frc177",
            year=2015,
            team=ndb.Key(Team, "frc177"),
            district_key=None,
        )
        self.new_district_team = DistrictTeam(
            id="2015ne_frc177",
            year=2015,
            team=ndb.Key(Team, "frc177"),
            district_key=ndb.Key(District, "2015ne"),
        )

    def assertMergedDistrictTeam(self, district_team: DistrictTeam) -> None:
        self.assertOldDistrictTeam(district_team)
        self.assertEqual(district_team.district_key, ndb.Key(District, "2015ne"))

    def assertOldDistrictTeam(self, district_team: DistrictTeam) -> None:
        self.assertEqual(district_team.year, 2015)
        self.assertEqual(district_team.team, ndb.Key(Team, "frc177"))

    def test_createOrUpdate(self) -> None:
        DistrictTeamManipulator.createOrUpdate(self.old_district_team)
        self.assertOldDistrictTeam(DistrictTeam.get_by_id("2015ne_frc177"))
        DistrictTeamManipulator.createOrUpdate(self.new_district_team)
        self.assertMergedDistrictTeam(DistrictTeam.get_by_id("2015ne_frc177"))

    def test_findOrSpawn(self) -> None:
        self.old_district_team.put()
        self.assertMergedDistrictTeam(
            DistrictTeamManipulator.findOrSpawn(self.new_district_team)
        )

    def test_updateMerge(self) -> None:
        self.assertMergedDistrictTeam(
            DistrictTeamManipulator.updateMerge(
                self.new_district_team, self.old_district_team
            )
        )
