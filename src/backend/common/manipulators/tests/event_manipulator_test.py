import datetime
import json
import unittest
from typing import Optional
from unittest.mock import patch

import pytest
import six
from google.appengine.ext import deferred
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.consts.event_type import EventType
from backend.common.helpers.location_helper import LocationHelper
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.models.event import Event


@pytest.mark.usefixtures("ndb_context")
class TestEventManipulator(unittest.TestCase):
    taskqueue_stub: Optional[testbed.taskqueue_stub.TaskQueueServiceStub] = None

    @pytest.fixture(autouse=True)
    def store_taskqueue_stub(self, taskqueue_stub):
        self.taskqueue_stub = taskqueue_stub

    def setUp(self):
        self.old_event = Event(
            id="2011ct",
            end_date=datetime.datetime(2011, 4, 2, 0, 0),
            event_short="ct",
            event_type_enum=EventType.REGIONAL,
            district_key=None,
            first_eid="5561",
            name="Northeast Utilities FIRST Connecticut Regional",
            start_date=datetime.datetime(2011, 3, 31, 0, 0),
            year=2011,
            venue_address="Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website="http://www.ctfirst.org/ctr",
            webcast_json=json.dumps([{"type": "twitch", "channel": "bar"}]),
        )

        self.new_event = Event(
            id="2011ct",
            end_date=datetime.datetime(2011, 4, 2, 0, 0),
            event_short="ct",
            event_type_enum=EventType.REGIONAL,
            district_key=None,
            first_eid="5561",
            name="Northeast Utilities FIRST Connecticut Regional",
            start_date=datetime.datetime(2011, 3, 31, 0, 0),
            year=2011,
            venue_address="Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website="http://www.ctfirst.org/ctr",
            facebook_eid="7",
            webcast_json=json.dumps([{"type": "ustream", "channel": "foo"}]),
        )

    def assertMergedEvent(self, event: Event) -> None:
        self.assertOldEvent(event)
        self.assertEqual(event.facebook_eid, "7")
        self.assertEqual(event.webcast[0]["type"], "twitch")
        self.assertEqual(event.webcast[0]["channel"], "bar")
        self.assertEqual(event.webcast[1]["type"], "ustream")
        self.assertEqual(event.webcast[1]["channel"], "foo")

    def assertOldEvent(self, event: Event) -> None:
        self.assertEqual(event.key.id(), "2011ct")
        self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event.event_type_enum, EventType.REGIONAL)
        self.assertEqual(event.district_key, None)
        self.assertEqual(event.start_date, datetime.datetime(2011, 3, 31, 0, 0))
        self.assertEqual(event.end_date, datetime.datetime(2011, 4, 2, 0, 0))
        self.assertEqual(event.year, 2011)
        self.assertEqual(
            event.venue_address,
            "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
        )
        self.assertEqual(event.website, "http://www.ctfirst.org/ctr")
        self.assertEqual(event.event_short, "ct")

    def test_createOrUpdate(self):
        EventManipulator.createOrUpdate(self.old_event)
        self.assertOldEvent(Event.get_by_id("2011ct"))
        EventManipulator.createOrUpdate(self.new_event)
        self.assertMergedEvent(Event.get_by_id("2011ct"))

    def test_findOrSpawn(self):
        self.old_event.put()
        self.assertMergedEvent(EventManipulator.findOrSpawn(self.new_event))

    def test_updateMerge(self):
        self.assertMergedEvent(
            EventManipulator.updateMerge(self.new_event, self.old_event)
        )

    def test_updateWebcast_noUnion(self):
        EventManipulator.createOrUpdate(self.old_event)
        self.assertOldEvent(Event.get_by_id("2011ct"))
        EventManipulator.createOrUpdate(self.new_event, auto_union=False)
        check = Event.get_by_id("2011ct")
        self.assertEqual(check.webcast, self.new_event.webcast)

    @patch.object(LocationHelper, "update_event_location")
    def test_update_location_on_update(self, update_location_mock) -> None:
        self.old_event.city = "Hartford"
        self.old_event.state_prov = "CT"
        self.old_event.country = "USA"
        assert self.old_event.timezone_id is None

        EventManipulator.createOrUpdate(self.old_event)

        def update_side_effect(event):
            event.timezone_id = "America/New_York"
            event.put()

        update_location_mock.side_effect = update_side_effect

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            # This lets us ensure that the devserver can run our task
            # See https://github.com/GoogleCloudPlatform/appengine-python-standard/issues/45
            six.ensure_text(task.payload)
            deferred.run(task.payload)

        assert none_throws(Event.get_by_id("2011ct")).timezone_id is not None
