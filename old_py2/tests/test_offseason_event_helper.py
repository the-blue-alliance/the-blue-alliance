import datetime
import json
import unittest2

from google.appengine.ext import testbed

from consts.event_type import EventType
from consts.district_type import DistrictType

from helpers.event.offseason_event_helper import OffseasonEventHelper
from models.event import Event


class TestOffseasonEventHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_is_direct_match_key_name(self):
        first_event_match = Event(year=2020, event_short='zor')
        second_event_match = Event(year=2020, event_short='zor')
        third_event_match = Event(year=2020, event_short='iri')

        self.assertTrue(OffseasonEventHelper.is_direct_match(first_event_match, second_event_match))
        self.assertFalse(OffseasonEventHelper.is_direct_match(first_event_match, third_event_match))

    def test_is_direct_match_key_name(self):
        tba_event_one = Event(year=2020, first_code='zor', event_short='zorr')
        tba_event_two = Event(year=2020, first_code='iri', event_short='irii')
        first_event = Event(year=2020, event_short='zor')

        self.assertTrue(OffseasonEventHelper.is_direct_match(tba_event_one, first_event))
        self.assertFalse(OffseasonEventHelper.is_direct_match(tba_event_two, first_event))

    def test_is_maybe_match(self):
        event_one = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        event_two = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        self.assertTrue(OffseasonEventHelper.is_maybe_match(event_one, event_two))

    def test_is_maybe_match_wrong_start(self):
        event_one = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        event_two = Event(
            start_date=datetime.datetime(year=2020, month=7, day=13, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        self.assertFalse(OffseasonEventHelper.is_maybe_match(event_one, event_two))
        event_two.start_date = event_one.start_date
        self.assertTrue(OffseasonEventHelper.is_maybe_match(event_one, event_two))

    def test_is_maybe_match_wrong_end(self):
        event_one = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        event_two = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=16, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        self.assertFalse(OffseasonEventHelper.is_maybe_match(event_one, event_two))
        event_two.end_date = event_one.end_date
        self.assertTrue(OffseasonEventHelper.is_maybe_match(event_one, event_two))

    def test_is_maybe_match_wrong_city(self):
        event_one = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        event_two = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="Sandusky",
            state_prov="OH"
        )
        self.assertFalse(OffseasonEventHelper.is_maybe_match(event_one, event_two))
        event_two.city = event_one.city
        self.assertTrue(OffseasonEventHelper.is_maybe_match(event_one, event_two))

    def test_is_maybe_match_wrong_state_prov(self):
        event_one = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="OH"
        )
        event_two = Event(
            start_date=datetime.datetime(year=2020, month=7, day=14, hour=0, minute=0, second=0),
            end_date=datetime.datetime(year=2020, month=7, day=15, hour=23, minute=59, second=59),
            city="London",
            state_prov="CA"
        )
        self.assertFalse(OffseasonEventHelper.is_maybe_match(event_one, event_two))
        event_two.state_prov = event_one.state_prov
        self.assertTrue(OffseasonEventHelper.is_maybe_match(event_one, event_two))

    def test_categorize_offseasons(self):
        # Setup some existing TBA events in the database - these will be queried for our test
        preseason_event = Event(
            id="2016mipre",
            name="Michigan Preseason Event",
            event_type_enum=EventType.PRESEASON,
            event_district_enum=DistrictType.MICHIGAN,
            short_name="MI Preseason",
            event_short="mipre",
            first_code="mierp",
            year=2016,
            end_date=datetime.datetime(2016, 02, 25),
            official=False,
            city='Anytown',
            state_prov='MI',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Anytown, MI, USA",
            timezone_id="America/New_York",
            start_date=datetime.datetime(2016, 02, 24),
            webcast_json="",
            website=None
        )
        preseason_event.put()

        offseason_event = Event(
            id="2016mioff",
            name="Michigan Offseason Event",
            event_type_enum=EventType.OFFSEASON,
            event_district_enum=DistrictType.MICHIGAN,
            short_name="MI Offseason",
            event_short="mioff",
            year=2016,
            end_date=datetime.datetime(2016, 06, 25),
            official=False,
            city='Anytown',
            state_prov='MI',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Anytown, MI, USA",
            timezone_id="America/New_York",
            start_date=datetime.datetime(2016, 06, 24),
            webcast_json="",
            website=None
        )
        offseason_event.put()

        # Exact match
        first_preseason = Event(
            year=2016,
            event_short="mierp"
        )
        # Indirect match
        first_offseason = Event(
            year=2016,
            event_short="miffo",
            start_date=datetime.datetime(2016, 06, 24),
            end_date=datetime.datetime(2016, 06, 25),
            city='Anytown',
            state_prov='MI',
        )
        first_new_event = Event(
            year=2016,
            event_short="minew"
        )
        first_events = [first_preseason, first_offseason, first_new_event]

        existing, new = OffseasonEventHelper.categorize_offseasons(2016, first_events)
        # Should have two existing events
        self.assertEqual(len(existing), 2)
        self.assertTrue((preseason_event, first_preseason) in existing)
        self.assertTrue((offseason_event, first_offseason) in existing)

        # Should have one new event
        self.assertEqual(len(new), 1)
        self.assertEqual(new, [first_new_event])

    def test_categorize_offseasons_no_events(self):
        first_preseason = Event(
            year=2016,
            event_short="mierp"
        )
        first_offseason = Event(
            year=2016,
            event_short="miffo",
            start_date=datetime.datetime(2016, 06, 24),
            end_date=datetime.datetime(2016, 06, 25),
            city='Anytown',
            state_prov='MI',
        )
        first_new_event = Event(
            year=2016,
            event_short="minew"
        )
        first_events = [first_preseason, first_offseason, first_new_event]

        existing, new = OffseasonEventHelper.categorize_offseasons(2016, first_events)
        # Should have no existing events
        self.assertEqual(len(existing), 0)
        self.assertEqual(len(new), 3)
