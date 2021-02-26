import unittest

import pytest

from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.models.district import District


@pytest.mark.usefixtures("ndb_context")
class TestDistrictManipulator(unittest.TestCase):
    def setUp(self):
        self.old_district = District(id="2014ne", year=2014, display_name="")

        self.new_district = District(
            id="2014ne",
            year=2014,
            display_name="New England",
        )

    def assertMergedDistrict(self, district: District) -> None:
        self.assertOldDistrict(district)
        self.assertEqual(district.display_name, "New England")

    def assertOldDistrict(self, district: District) -> None:
        self.assertEqual(district.year, 2014)

    def test_createOrUpdate(self) -> None:
        DistrictManipulator.createOrUpdate(self.old_district)
        self.assertOldDistrict(District.get_by_id("2014ne"))
        DistrictManipulator.createOrUpdate(self.new_district)
        self.assertMergedDistrict(District.get_by_id("2014ne"))

    def test_findOrSpawn(self) -> None:
        self.old_district.put()
        self.assertMergedDistrict(DistrictManipulator.findOrSpawn(self.new_district))

    def test_updateMerge(self) -> None:
        self.assertMergedDistrict(
            DistrictManipulator.updateMerge(self.new_district, self.old_district)
        )
