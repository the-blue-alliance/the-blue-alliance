import unittest

import pytest

from backend.common.deferred.clients.fake_client import FakeTaskClient
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.models.district import District


@pytest.mark.usefixtures("ndb_context")
class TestDistrictManipulator(unittest.TestCase):
    def setUp(self):
        self.task_client = FakeTaskClient()
        self.task_client.flush()

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

    def test_update_name_from_last_year_on_create(self) -> None:
        District(
            id="2015ne",
            abbreviation="ne",
            year=2015,
            display_name="New England",
        ).put()

        updated = DistrictManipulator.createOrUpdate(
            District(id="2016ne", abbreviation="ne", year=2016)
        )
        # We didn't originally specify a display name
        assert updated.display_name is None

        # But the update hook should add it in from the prior year's
        self.task_client.drain_pending_jobs("post-update-hooks")
        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.display_name == "New England"

    def test_do_not_update_name_from_last_year_on_update(self) -> None:
        District(
            id="2015ne", abbreviation="ne", year=2015, display_name="New England"
        ).put()
        District(
            id="2016ne",
            abbreviation="ne",
            year=2016,
        ).put()

        updated = DistrictManipulator.createOrUpdate(
            District(id="2016ne", abbreviation="ne", year=2016)
        )
        # We didn't originally specify a display name
        assert updated.display_name is None

        # But the update hook should have skipped adding it
        self.task_client.drain_pending_jobs("post-update-hooks")
        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.display_name is None

    def test_district_name_get_backported(self) -> None:
        District(
            id="2015ne",
            abbreviation="ne",
            year=2015,
            display_name="Old Name",
        ).put()
        District(
            id="2016ne",
            abbreviation="ne",
            year=2016,
        ).put()

        updated = DistrictManipulator.createOrUpdate(
            District(
                id="2016ne",
                display_name="New Name",
            )
        )
        assert updated.display_name == "New Name"

        # The update hook should have also set the name for 2015
        self.task_client.drain_pending_jobs("post-update-hooks")
        district = District.get_by_id("2015ne")
        assert district is not None
        assert district.display_name == "New Name"
