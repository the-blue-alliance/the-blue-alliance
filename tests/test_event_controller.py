import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.event_type import EventType
from controllers.event_controller import EventDetail, EventInsights, EventList
from models.district import District
from models.event import Event
from models.event_details import EventDetails


class TestEventController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/event/<event_key>', EventDetail, 'event-detail'),
            RedirectRoute(r'/event/<event_key>/insights', EventInsights, 'event-insights'),
            RedirectRoute(r'/events/<year:[0-9]+>', EventList, 'event-list-year'),
            RedirectRoute(r'/events', EventList, 'event-list'),
        ])
        self.testapp = webtest.TestApp(app)

        self.district = District(
            id='2016ne',
            abbreviation='ne',
            year=2016,
            display_name='New England'
        )
        self.district.put()

        self.event1 = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            district_key=ndb.Key(District, '2016ne'),
            short_name="New England",
            event_short="necmp",
            year=2016,
            end_date=datetime(2016, 03, 27),
            official=True,
            city='Hartford',
            state_prov='CT',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2016, 03, 24),
            webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
            website="http://www.firstsv.org"
        )
        self.event1.put()

        # To test that /events defaults to current year
        this_year = datetime.now().year
        self.event2 = Event(
            id="{}necmp".format(this_year),
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            district_key=ndb.Key(District, '2016ne'),
            short_name="New England",
            event_short="necmp",
            year=this_year,
            end_date=datetime(this_year, 03, 27),
            official=True,
            city='Hartford',
            state_prov='CT',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(this_year, 03, 24),
            webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
            website="http://www.firstsv.org"
        )
        self.event2.put()

        self.event1_details = EventDetails(
            id=self.event1.key.id(),
            predictions={"ranking_prediction_stats": {'qual': None, 'playoff': None}, "match_predictions": {'qual': None, 'playoff': None}, "ranking_predictions": None, "match_prediction_stats": {'qual': None, 'playoff': None}}
        )
        self.event1_details.put()

        self.event2_details = EventDetails(
            id=self.event2.key.id(),
            predictions={"ranking_prediction_stats": {'qual': None, 'playoff': None}, "match_predictions": {'qual': None, 'playoff': None}, "ranking_predictions": None, "match_prediction_stats": {'qual': None, 'playoff': None}}
        )
        self.event2_details.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_event_list_default_year(self):
        response = self.testapp.get("/events")
        self.assertEqual(response.status_int, 200)

    def test_event_list_explicit_year(self):
        response = self.testapp.get("/events/2015")
        self.assertEqual(response.status_int, 200)

    def test_event_list_no_events(self):
        response = self.testapp.get("/events/2014")
        self.assertEqual(response.status_int, 200)

    def test_event_details(self):
        response = self.testapp.get("/event/2016necmp")
        self.assertEqual(response.status_int, 200)

    def test_event_details_not_found(self):
        response = self.testapp.get("/event/2016meow", status=404)
        self.assertEqual(response.status_int, 404)

    def test_event_insights(self):
        response = self.testapp.get("/event/2016necmp/insights")
        self.assertEqual(response.status_int, 200)

    def test_event_insights_not_found(self):
        response = self.testapp.get("/event/2016meow/insights", status=404)
        self.assertEqual(response.status_int, 404)
