import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.award_type import AwardType
from consts.event_type import EventType
from helpers.event.event_test_creator import EventTestCreator
from models.award import Award
from models.event import Event
from models.team import Team

from mocks.models.mock_event import MockEvent


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

    def test_week_str_none(self):
        event_week_none = MockEvent(week=None, year=2012)
        self.assertIsNone(event_week_none.week_str)

    def test_week_str_2016(self):
        event_week_0_year_2016 = MockEvent(week=0, year=2016)
        self.assertEqual(event_week_0_year_2016.week_str, "Week 0.5")
        event_week_1_year_2016 = MockEvent(week=1, year=2016)
        self.assertEqual(event_week_1_year_2016.week_str, "Week 1")

    def test_week_str_not_2016(self):
        event_week_0_year_2012 = MockEvent(week=0, year=2012)
        self.assertEqual(event_week_0_year_2012.week_str, "Week 1")
        event_week_1_year_2022 = MockEvent(week=1, year=2022)
        self.assertEqual(event_week_1_year_2022.week_str, "Week 2")

    def test_in_season(self):
        for event_type in EventType.type_names.keys():
            event = Event(event_type_enum=event_type)
            if event_type in EventType.SEASON_EVENT_TYPES:
                self.assertTrue(event.is_in_season)
            else:
                self.assertFalse(event.is_in_season)

    def test_offseason(self):
        for event_type in EventType.type_names.keys():
            event = Event(event_type_enum=event_type)
            if event_type in EventType.SEASON_EVENT_TYPES:
                self.assertFalse(event.is_offseason)
            else:
                self.assertTrue(event.is_offseason)

    def test_team_awards_none(self):
        self.assertEqual(self.event_ends_today.team_awards(), {})

    def test_team_awards(self):
        # Insert some Teams
        frc1 = Team(
            id='frc1',
            team_number=1
        )
        frc1.put()
        frc2 = Team(
            id='frc2',
            team_number=2
        )
        frc2.put()
        frc3 = Team(
            id='frc3',
            team_number=3
        )
        frc3.put()
        # Insert some Awards for some Teams
        award = Award(
            id=Award.render_key_name(self.event_ends_today.key_name, AwardType.INDUSTRIAL_DESIGN),
            name_str='Industrial Design Award sponsored by General Motors',
            award_type_enum=AwardType.INDUSTRIAL_DESIGN,
            event=self.event_ends_today.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, 'frc1')],
            year=2020
        )
        award.put()
        winner_award = Award(
            id=Award.render_key_name(self.event_ends_today.key_name, AwardType.WINNER),
            name_str='Regional Event Winner',
            award_type_enum=AwardType.WINNER,
            event=self.event_ends_today.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, 'frc2'), ndb.Key(Team, 'frc1')],
            year=2020
        )
        winner_award.put()

        self.assertItemsEqual(self.event_ends_today.team_awards().keys(), [frc1.key, frc2.key])
