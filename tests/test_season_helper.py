from datetime import datetime, timedelta
from pytz import timezone, UTC
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from helpers.season_helper import SeasonHelper
from models.event import Event


class TestSeasonHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_effective_season_year_no_events(self):
        now = datetime.now()
        self.assertEqual(SeasonHelper.effective_season_year(), now.year)

    def test_effective_season_year_this_year(self):
        # Effective season should be this year
        today = datetime.today()
        Event(
            id="{}testendstomorrow".format(today.year),
            end_date=today + timedelta(days=1),
            event_short="testendstomorrow",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Ends Tomorrow)",
            start_date=today,
            year=today.year,
            venue_address="123 Fake Street, Anytown, MI, USA",
            website="http://www.google.com"
        ).put()
        self.assertEqual(SeasonHelper.effective_season_year(), today.year)

    def test_effective_season_year_next_year(self):
        # Effective season should be next year
        today = datetime.today()
        Event(
            id="{}testended".format(today.year),
            end_date=today - timedelta(days=1),
            event_short="testended",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Ends Tomorrow)",
            start_date=today - timedelta(days=2),
            year=today.year,
            venue_address="123 Fake Street, Anytown, MI, USA",
            website="http://www.google.com"
        ).put()
        self.assertEqual(SeasonHelper.effective_season_year(), today.year + 1)

    def test_effective_season_year_next_year_ignore_non_official(self):
        # Effective season should be next year
        today = datetime.today()
        # Insert an event that has already happened - otherwise we'll default to the current season
        # This is to simulate offseason
        Event(
            id="{}testended".format(today.year),
            end_date=today - timedelta(days=1),
            event_short="testended",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Test Event (Ends Tomorrow)",
            start_date=today - timedelta(days=2),
            year=today.year,
            venue_address="123 Fake Street, Anytown, MI, USA",
            website="http://www.google.com"
        ).put()
        Event(
            id="{}testendstomorrow".format(today.year),
            end_date=today + timedelta(days=1),
            event_short="testendstomorrow",
            event_type_enum=EventType.OFFSEASON,
            first_eid="5561",
            name="Test Event (Ends Tomorrow)",
            start_date=today,
            year=today.year,
            venue_address="123 Fake Street, Anytown, MI, USA",
            website="http://www.google.com"
        ).put()
        self.assertEqual(SeasonHelper.effective_season_year(), today.year + 1)

    def test_is_kickoff_at_least_one_day_away(self):
        a = datetime(2020, 1, 3, 14, 30, 00, tzinfo=UTC)  # False - over one day
        b = datetime(2020, 1, 3, 15, 30, 00, tzinfo=UTC)  # True - exactly one day
        c = datetime(2020, 1, 4, 15, 30, 00, tzinfo=UTC)  # True - same time
        d = datetime(2020, 2, 4, 15, 30, 00, tzinfo=UTC)  # True - very far away in the future
        expected_results = [False, True, True, True]

        for (date, result) in zip([a, b, c, d], expected_results):
            at_least_one_day_away = SeasonHelper.is_kickoff_at_least_one_day_away(date, 2020)
            self.assertEqual(at_least_one_day_away, result)

    def test_kickoff_datetime(self):
        # 2011 - Saturday the 8th (https://en.wikipedia.org/wiki/Logo_Motion)
        kickoff_2011 = datetime(2011, 1, 8, 10, 30, 00, tzinfo=timezone('EST'))
        kickoff_2011_utc = kickoff_2011.astimezone(UTC)
        self.assertEqual(SeasonHelper.kickoff_datetime_est(year=2011), kickoff_2011)
        self.assertEqual(SeasonHelper.kickoff_datetime_utc(year=2011), kickoff_2011_utc)
        # 2010 - Saturday the 9th (https://en.wikipedia.org/wiki/Breakaway_(FIRST))
        kickoff_2010 = datetime(2010, 1, 9, 10, 30, 00, tzinfo=timezone('EST'))
        kickoff_2010_utc = kickoff_2010.astimezone(UTC)
        self.assertEqual(SeasonHelper.kickoff_datetime_est(year=2010), kickoff_2010)
        self.assertEqual(SeasonHelper.kickoff_datetime_utc(year=2010), kickoff_2010_utc)
        # 2009 - Saturday the 3rd (https://en.wikipedia.org/wiki/Lunacy_(FIRST)
        kickoff_2009 = datetime(2009, 1, 3, 10, 30, 00, tzinfo=timezone('EST'))
        kickoff_2009_utc = kickoff_2009.astimezone(UTC)
        self.assertEqual(SeasonHelper.kickoff_datetime_est(year=2009), kickoff_2009)
        self.assertEqual(SeasonHelper.kickoff_datetime_utc(year=2009), kickoff_2009_utc)
