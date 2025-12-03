import datetime
import json
from typing import Optional
from unittest.mock import patch

import pytest
import six
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.helpers.location_helper import LocationHelper
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.models.event import Event
from backend.common.models.location import Location


@pytest.fixture
def old_event() -> Event:
    return Event(
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


@pytest.fixture
def new_event() -> Event:
    return Event(
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


def assert_merged_event(event: Event) -> None:
    assert_old_event(event)
    assert event.facebook_eid == "7"
    assert event.webcast[0]["type"] == "twitch"
    assert event.webcast[0]["channel"] == "bar"
    assert event.webcast[1]["type"] == "ustream"
    assert event.webcast[1]["channel"] == "foo"


def assert_old_event(event: Event) -> None:
    assert event.key.id() == "2011ct"
    assert event.name == "Northeast Utilities FIRST Connecticut Regional"
    assert event.event_type_enum == EventType.REGIONAL
    assert event.district_key is None
    assert event.start_date == datetime.datetime(2011, 3, 31, 0, 0)
    assert event.end_date == datetime.datetime(2011, 4, 2, 0, 0)
    assert event.year == 2011
    assert (
        event.venue_address
        == "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA"
    )
    assert event.website == "http://www.ctfirst.org/ctr"
    assert event.event_short == "ct"


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
def test_createOrUpdate(old_event: Event, new_event: Event) -> None:
    EventManipulator.createOrUpdate(old_event)
    assert_old_event(Event.get_by_id("2011ct"))
    EventManipulator.createOrUpdate(new_event)
    assert_merged_event(Event.get_by_id("2011ct"))


@pytest.mark.usefixtures("ndb_context")
def test_findOrSpawn(old_event: Event, new_event: Event) -> None:
    old_event.put()
    assert_merged_event(EventManipulator.findOrSpawn(new_event))


@pytest.mark.usefixtures("ndb_context")
def test_updateMerge(old_event: Event, new_event: Event) -> None:
    assert_merged_event(EventManipulator.updateMerge(new_event, old_event))


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
def test_updateWebcast_noUnion(old_event: Event, new_event: Event) -> None:
    EventManipulator.createOrUpdate(old_event)
    assert_old_event(Event.get_by_id("2011ct"))
    EventManipulator.createOrUpdate(new_event, auto_union=False)
    check = Event.get_by_id("2011ct")
    assert check.webcast == new_event.webcast


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
@pytest.mark.parametrize("official", [True, False])
@patch.object(LocationHelper, "get_timezone_id")
@patch.object(LocationHelper, "update_event_location")
def test_update_location_official_event(
    update_location_mock,
    get_timezone_id_mock,
    official: bool,
    old_event: Event,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    old_event.official = official

    EventManipulator.createOrUpdate(old_event)

    def update_side_effect(event):
        event.normalized_location = Location(
            lat_lng=ndb.GeoPt(37.335480, -121.893028),
        )
        event.put()

    update_location_mock.side_effect = update_side_effect

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    update_location_mock.assert_called_once()

    if official:
        get_timezone_id_mock.assert_not_called()
    else:
        get_timezone_id_mock.assert_called_once()


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
@patch.object(LocationHelper, "update_event_location")
def test_update_location_on_update(
    update_location_mock,
    old_event: Event,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    old_event.city = "Hartford"
    old_event.state_prov = "CT"
    old_event.country = "USA"
    assert old_event.timezone_id is None

    EventManipulator.createOrUpdate(old_event)

    def update_side_effect(event):
        event.timezone_id = "America/New_York"
        event.put()

    update_location_mock.side_effect = update_side_effect

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        # This lets us ensure that the devserver can run our task
        # See https://github.com/GoogleCloudPlatform/appengine-python-standard/issues/45
        six.ensure_text(task.payload)
        run_from_task(task)

    assert none_throws(Event.get_by_id("2011ct")).timezone_id is not None
