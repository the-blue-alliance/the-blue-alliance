from datetime import datetime, timedelta, date
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

    def test_stop_build_date(self):
        # 2019 - Feb 19th, 2019
        stop_build_2019 = datetime(2019, 2, 19, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2019_utc = stop_build_2019.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2019), stop_build_2019)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2019), stop_build_2019_utc)
        # 2018 - Feb 20th, 2018
        stop_build_2018 = datetime(2018, 2, 20, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2018_utc = stop_build_2018.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2018), stop_build_2018)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2018), stop_build_2018_utc)
        # 2017 - Feb 21th, 2017
        stop_build_2017 = datetime(2017, 2, 21, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2017_utc = stop_build_2017.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2017), stop_build_2017)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2017), stop_build_2017_utc)
        # 2016 - Feb 23th, 2016
        stop_build_2016 = datetime(2016, 2, 23, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2016_utc = stop_build_2016.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2016), stop_build_2016)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2016), stop_build_2016_utc)

    def test_competition_season_start_date(self):
        # 2020 - Feb 24th, 2020
        comp_season_2020 = date(2020, 2, 24)
        self.assertEqual(SeasonHelper.competition_season_start_date(year=2020), comp_season_2020)
        # 2019 - Feb 25th, 2019
        comp_season_2019 = date(2019, 2, 25)
        self.assertEqual(SeasonHelper.competition_season_start_date(year=2019), comp_season_2019)
        # 2018 - Feb 26th, 2018
        comp_season_2018 = date(2018, 2, 26)
        self.assertEqual(SeasonHelper.competition_season_start_date(year=2018), comp_season_2018)
        # 2017 - Mar 1st, 2017
        comp_season_2017 = date(2017, 3, 1)
        self.assertEqual(SeasonHelper.competition_season_start_date(year=2017), comp_season_2017)
        # 2016 - Mar 2nd, 2016
        comp_season_2016 = date(2016, 3, 2)
        self.assertEqual(SeasonHelper.competition_season_start_date(year=2016), comp_season_2016)
