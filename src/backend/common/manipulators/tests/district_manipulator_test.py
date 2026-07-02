import unittest
from typing import Optional

import pytest
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.helpers.deferred import run_from_task
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.models.district import District


@pytest.mark.usefixtures("ndb_context")
class TestDistrictManipulator(unittest.TestCase):
    taskqueue_stub: Optional[testbed.taskqueue_stub.TaskQueueServiceStub] = None

    @pytest.fixture(autouse=True)
    def store_taskqueue_stub(self, taskqueue_stub):
        self.taskqueue_stub = taskqueue_stub

    def setUp(self):
        self.old_district = District(
            id="2014ne", year=2014, display_name="", abbreviation="ne"
        )

        self.new_district = District(
            id="2014ne",
            year=2014,
            display_name="New England",
            abbreviation="ne",
        )

    def assertMergedDistrict(self, district: District) -> None:
        self.assertOldDistrict(district)
        self.assertEqual(district.display_name, "New England")

    def assertOldDistrict(self, district: District) -> None:
        self.assertEqual(district.year, 2014)

    def test_createOrUpdate(self) -> None:
        DistrictManipulator.createOrUpdate(self.old_district)
        self.assertOldDistrict(none_throws(District.get_by_id("2014ne")))
        DistrictManipulator.createOrUpdate(self.new_district)
        self.assertMergedDistrict(none_throws(District.get_by_id("2014ne")))

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
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

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
            District(id="2016ne", abbreviation="ne", elasticsearch_name="NE", year=2016)
        )
        # We didn't originally specify a display name
        assert updated.display_name is None

        # But the update hook should have skipped adding it
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

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
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        district = District.get_by_id("2015ne")
        assert district is not None
        assert district.display_name == "New Name"

    def test_update_webcast_unit_from_last_year_on_create(self) -> None:
        District(
            id="2015ne",
            abbreviation="ne",
            year=2015,
            display_name="New England",
            uses_official_webcast_unit=True,
        ).put()

        updated = DistrictManipulator.createOrUpdate(
            District(id="2016ne", abbreviation="ne", year=2016)
        )
        # We didn't originally specify uses_official_webcast_unit
        assert updated.uses_official_webcast_unit is None

        # But the update hook should add it in from the prior year's
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.uses_official_webcast_unit is True

    def test_no_webcast_unit_propagation_when_last_year_false(self) -> None:
        District(
            id="2015ne",
            abbreviation="ne",
            year=2015,
            display_name="New England",
            uses_official_webcast_unit=False,
        ).put()

        DistrictManipulator.createOrUpdate(
            District(id="2016ne", abbreviation="ne", year=2016)
        )

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.uses_official_webcast_unit is None

    def test_update_webcast_channels_from_last_year_on_create(self) -> None:
        District(
            id="2015ne",
            abbreviation="ne",
            year=2015,
            display_name="New England",
            webcast_channels=[
                {
                    "type": "youtube",
                    "channel": "FIRST in Michigan",
                    "channel_id": "UC1234567890",
                }
            ],
        ).put()

        updated = DistrictManipulator.createOrUpdate(
            District(id="2016ne", abbreviation="ne", year=2016)
        )
        # We didn't originally specify webcast_channels
        assert updated.webcast_channels == []

        # But the update hook should add it in from the prior year's
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.webcast_channels is not None
        assert len(district.webcast_channels) == 1
        assert district.webcast_channels[0]["channel"] == "FIRST in Michigan"
        assert district.webcast_channels[0]["channel_id"] == "UC1234567890"

    def test_no_webcast_channels_propagation_when_already_set(self) -> None:
        District(
            id="2015ne",
            abbreviation="ne",
            year=2015,
            display_name="New England",
            webcast_channels=[
                {
                    "type": "youtube",
                    "channel": "Old Channel",
                    "channel_id": "UC_old",
                }
            ],
        ).put()

        DistrictManipulator.createOrUpdate(
            District(
                id="2016ne",
                abbreviation="ne",
                year=2016,
                webcast_channels=[
                    {
                        "type": "youtube",
                        "channel": "New Channel",
                        "channel_id": "UC_new",
                    }
                ],
            )
        )

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.webcast_channels is not None
        assert len(district.webcast_channels) == 1
        # Should still have the new channel, not the old one
        assert district.webcast_channels[0]["channel"] == "New Channel"
        assert district.webcast_channels[0]["channel_id"] == "UC_new"

    def test_webcast_channels_not_wiped_by_empty_update(self) -> None:
        """Regression test: FRC API updates produce a District with no webcast_channels
        (empty list). The manipulator should NOT overwrite admin-set channels with [].
        """
        District(
            id="2016ne",
            abbreviation="ne",
            year=2016,
            display_name="New England",
            webcast_channels=[
                {
                    "type": "youtube",
                    "channel": "FIRST in Michigan",
                    "channel_id": "UC1234567890",
                }
            ],
        ).put()

        # Simulate an FRC API update: new model has no webcast_channels set
        DistrictManipulator.createOrUpdate(
            District(
                id="2016ne",
                abbreviation="ne",
                year=2016,
                display_name="New England Updated",
            )
        )

        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.display_name == "New England Updated"
        # webcast_channels must NOT have been wiped
        assert district.webcast_channels is not None
        assert len(district.webcast_channels) == 1
        assert district.webcast_channels[0]["channel_id"] == "UC1234567890"

    def test_uses_official_webcast_unit_not_wiped_by_empty_update(self) -> None:
        """Regression test: FRC API updates create a District without uses_official_webcast_unit
        (None). The manipulator should NOT overwrite an admin-set True value with None.
        """
        District(
            id="2016ne",
            abbreviation="ne",
            year=2016,
            display_name="New England",
            uses_official_webcast_unit=True,
        ).put()

        # Simulate an FRC API update: new model has no uses_official_webcast_unit set
        DistrictManipulator.createOrUpdate(
            District(
                id="2016ne",
                abbreviation="ne",
                year=2016,
                display_name="New England Updated",
            )
        )

        district = District.get_by_id("2016ne")
        assert district is not None
        assert district.display_name == "New England Updated"
        # uses_official_webcast_unit must NOT have been wiped
        assert district.uses_official_webcast_unit is True
