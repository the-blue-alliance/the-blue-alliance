import unittest
from typing import Optional
from unittest.mock import patch

import pytest
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestEventDetailsManipulator(unittest.TestCase):
    taskqueue_stub: Optional[testbed.taskqueue_stub.TaskQueueServiceStub] = None

    @pytest.fixture(autouse=True)
    def store_taskqueue_stub(self, taskqueue_stub):
        self.taskqueue_stub = taskqueue_stub

    def setUp(self):
        self.old_alliance_selections = {
            "1": {"picks": ["frc254", "frc469", "frc2848", "frc74"], "declines": []},
            "2": {"picks": ["frc1718", "frc2451", "frc573", "frc2016"], "declines": []},
            "3": {"picks": ["frc2928", "frc2013", "frc1311", "frc842"], "declines": []},
            "4": {"picks": ["frc180", "frc125", "frc1323", "frc2468"], "declines": []},
            "5": {"picks": ["frc118", "frc359", "frc4334", "frc865"], "declines": []},
            "6": {"picks": ["frc135", "frc1241", "frc11", "frc68"], "declines": []},
            "7": {"picks": ["frc3478", "frc177", "frc294", "frc230"], "declines": []},
            "8": {"picks": ["frc624", "frc987", "frc3476", "frc123"], "declines": []},
        }

        self.new_alliance_selections = {
            "1": {"picks": ["frc254", "frc469", "frc2848", "frc74"], "declines": []},
            "2": {"picks": ["frc1718", "frc2451", "frc573", "frc2016"], "declines": []},
            "3": {"picks": ["frc2928", "frc2013", "frc1311", "frc842"], "declines": []},
            "4": {"picks": ["frc180", "frc125", "frc1323", "frc2468"], "declines": []},
            "5": {"picks": ["frc118", "frc359", "frc4334", "frc865"], "declines": []},
            "6": {"picks": ["frc135", "frc1241", "frc11", "frc68"], "declines": []},
            "7": {"picks": ["frc3478", "frc177", "frc294", "frc230"], "declines": []},
            "8": {"picks": ["frc624", "frc987", "frc3476", "frc3015"], "declines": []},
        }

        self.event = Event(
            id="2011ct",
            event_short="ct",
            year=2011,
            event_type_enum=EventType.REGIONAL,
        )
        self.event.put()

        self.event2025 = Event(
            id="2025ct",
            event_short="ct",
            year=2025,
            event_type_enum=EventType.REGIONAL,
        )
        self.event2025.put()

        self.old_event_details = EventDetails(
            id="2011ct",
            alliance_selections=self.old_alliance_selections,
        )

        self.new_event_details = EventDetails(
            id="2011ct",
            alliance_selections=self.new_alliance_selections,
            matchstats={
                "oprs": {
                    "4255": 7.4877151786460301,
                    "2643": 27.285682906835952,
                    "852": 10.452538750544525,
                    "4159": 25.820137009871139,
                    "581": 18.513816255143144,
                }
            },
        )

        self.old_event_details2025 = EventDetails(
            id="2025ct",
            alliance_selections=self.old_alliance_selections,
        )

    def assertMergedEventDetails(self, event_details):
        self.assertOldEventDetails(event_details)
        self.assertEqual(
            event_details.matchstats,
            {
                "oprs": {
                    "4255": 7.4877151786460301,
                    "2643": 27.285682906835952,
                    "852": 10.452538750544525,
                    "4159": 25.820137009871139,
                    "581": 18.513816255143144,
                }
            },
        )
        self.assertEqual(
            event_details.alliance_selections, self.new_alliance_selections
        )

    def assertOldEventDetails(self, event_details):
        self.assertEqual(event_details.key.id(), "2011ct")

    def test_createOrUpdate(self):
        EventDetailsManipulator.createOrUpdate(self.old_event_details)
        self.assertOldEventDetails(EventDetails.get_by_id("2011ct"))
        EventDetailsManipulator.createOrUpdate(self.new_event_details)
        self.assertMergedEventDetails(EventDetails.get_by_id("2011ct"))

    def test_findOrSpawn(self):
        self.old_event_details.put()
        self.assertMergedEventDetails(
            EventDetailsManipulator.findOrSpawn(self.new_event_details)
        )

    def test_updateMerge(self):
        self.assertMergedEventDetails(
            EventDetailsManipulator.updateMerge(
                self.new_event_details, self.old_event_details
            )
        )

    def test_postUpdateHook_calcs(self):
        EventDetailsManipulator.createOrUpdate(self.old_event_details)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        # Ensure we have a district_points_calc test enqueued
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="default"
        )
        assert len(tasks) == 2

        assert tasks[0].url == "/tasks/math/do/event_team_status/2011ct"
        assert tasks[1].url == "/tasks/math/do/district_points_calc/2011ct"

    def test_postUpdateHook_calcs_regionalChampsPoints(self):
        EventDetailsManipulator.createOrUpdate(self.old_event_details2025)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        # Ensure we have a district_points_calc test enqueued
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="default"
        )
        assert len(tasks) == 3

        task_urls = {t.url for t in tasks}
        assert "/tasks/math/do/event_team_status/2025ct" in task_urls
        assert "/tasks/math/do/district_points_calc/2025ct" in task_urls
        assert "/tasks/math/do/regional_champs_pool_points_calc/2025ct" in task_urls

    def test_postUpdateHook_notifications(self):
        import datetime

        # Setup our event to be "now"
        self.event.start_date = datetime.datetime.now()
        self.event.end_date = self.event.start_date + datetime.timedelta(days=1)

        self.old_event_details.put()
        EventDetailsManipulator.createOrUpdate(self.new_event_details)

        # But the update hook should have skipped adding it
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1

        for task in tasks:
            run_from_task(task)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="push-notifications"
        )
        assert len(tasks) == 1
        task = tasks[0]
        assert task.name == "2011ct_alliance_selection"

    def test_postUpdateHook_notifications_notWithinADay(self):
        self.old_event_details.put()
        EventDetailsManipulator.createOrUpdate(self.new_event_details)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1

        for task in tasks:
            with patch.object(
                TBANSHelper, "alliance_selection"
            ) as mock_alliance_selection:
                run_from_task(task)

        # Event is not configured to be within a day - skip it
        mock_alliance_selection.assert_not_called()
