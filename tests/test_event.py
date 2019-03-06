import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from helpers.event.event_test_creator import EventTestCreator
from models.event import Event


class TestEvent(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.future_event = EventTestCreator.createFutureEvent(only_event=True)
        self.present_event = EventTestCreator.createPresentEvent(only_event=True)
        self.past_event = EventTestCreator.createPastEvent(only_event=True)
        self.event_starts_today = Event(
            id="{}teststartstoday".format(datetime.datetime.now().year),
            end_date=datetime.datetime.today() + datetime.timedelta(days=2),
            event_short="teststartstoday",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Starts Today)",
            start_date=datetime.datetime.today(),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com"
        )
        self.event_ends_today = Event(
            id="{}testendstoday".format(datetime.datetime.now().year),
            end_date=datetime.datetime.today(),
            event_short="testendstoday",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Ends Today)",
            start_date=datetime.datetime.today() - datetime.timedelta(days=2),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com"
        )
        self.event_starts_tomorrow = Event(
            id="{}teststartstomorrow".format(datetime.datetime.now().year),
            end_date=datetime.datetime.today() + datetime.timedelta(days=3),
            event_short="teststartstomorrow",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Starts Tomorrow)",
            start_date=datetime.datetime.today() + datetime.timedelta(days=1),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com"
        )
        self.event_starts_tomorrow_tz = Event(
            id="{}teststartstomorrow".format(datetime.datetime.now().year),
            end_date=datetime.datetime.today() + datetime.timedelta(days=3),
            event_short="teststartstomorrow",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Starts Tomorrow)",
            start_date=datetime.datetime.today() + datetime.timedelta(days=1),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com",
            timezone_id="America/New_York",
        )

    def tearDown(self):
        self.future_event.key.delete()
        self.present_event.key.delete()
        self.past_event.key.delete()

        self.testbed.deactivate()

    def test_dates_future(self):
        self.assertFalse(self.future_event.now)
        self.assertTrue(self.future_event.future)
        self.assertFalse(self.future_event.past)
        self.assertFalse(self.future_event.withinDays(0, 8))
        self.assertTrue(self.future_event.withinDays(-8, 0))

        self.assertFalse(self.event_starts_tomorrow.future)
        self.assertTrue(self.event_starts_tomorrow.now)
        self.assertFalse(self.event_starts_tomorrow.past)

        self.assertTrue(self.event_starts_tomorrow_tz.future)
        self.assertFalse(self.event_starts_tomorrow_tz.now)
        self.assertFalse(self.event_starts_tomorrow_tz.past)

    def test_dates_past(self):
        self.assertFalse(self.past_event.now)
        self.assertFalse(self.past_event.future)
        self.assertTrue(self.past_event.past)
        self.assertTrue(self.past_event.withinDays(0, 8))
        self.assertFalse(self.past_event.withinDays(-8, 0))

    def test_dates_present(self):
        self.assertTrue(self.present_event.now)
        self.assertTrue(self.present_event.withinDays(-1, 1))
        self.assertFalse(self.present_event.future)
        self.assertFalse(self.present_event.past)

    def test_dates_starts_today(self):
        self.assertTrue(self.event_starts_today.starts_today)
        self.assertFalse(self.event_starts_today.ends_today)

    def test_dates_ends_today(self):
        self.assertFalse(self.event_ends_today.starts_today)
        self.assertTrue(self.event_ends_today.ends_today)

    def test_week_str_no_week(self):
        event = Event(id="week_str_event_no_week", year=datetime.datetime.now().year)
        self.assertIsNone(event.week_str)

    def test_week_str_2016_week_0(self):
        event = Event(id="week_str_event_2016_week_0", year=2016, start_date=datetime.datetime.today())
        self.assertEqual(event.week_str, "Week 0.5")

    def test_week_str_2016(self):
        event = Event(id="week_str_event_2016", year=datetime.datetime.now().year, start_date=datetime.datetime.today())
        self.assertEqual(event.week_str, "Week 2")

    def test_week_str(self):
        event = Event(id="week_str_event", year=datetime.datetime.now().year, start_date=datetime.datetime.today())
        self.assertEqual(event.week_str, "Week 3")
