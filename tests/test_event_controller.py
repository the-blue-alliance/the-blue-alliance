from datetime import datetime

import unittest2
import webapp2
import webtest
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.event_controller import EventDetail, EventInsights, EventList
from models.event import Event


class TestEventController(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        app = webapp2.WSGIApplication([
            RedirectRoute(r'/event/<event_key>', EventDetail, 'event-detail'),
            RedirectRoute(r'/event/<event_key>/insights', EventInsights, 'event-insights'),
            RedirectRoute(r'/events/<year:[0-9]+>', EventList, 'event-list-year'),
            RedirectRoute(r'/events', EventList, 'event-list'),
        ])
        self.testapp = webtest.TestApp(app)

        self.event1 = Event(
                id="2016necmp",
                name="New England District Championship",
                event_type_enum=EventType.DISTRICT_CMP,
                event_district_enum=DistrictType.NEW_ENGLAND,
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
                website="http://www.firstsv.org",
                matchstats_json='{"ranking_prediction_stats": null, "match_predictions": null, "ranking_predictions": null, "match_prediction_stats": null}',
        )
        this_year = datetime.now().year
        self.event2 = Event(
                id="2016necmp",
                name="New England District Championship",
                event_type_enum=EventType.DISTRICT_CMP,
                event_district_enum=DistrictType.NEW_ENGLAND,
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
                website="http://www.firstsv.org",
                matchstats_json='{"ranking_prediction_stats": null, "match_predictions": null, "ranking_predictions": null, "match_prediction_stats": null}',
        )
        self.event1.put()
        self.event2.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testEventListDefaultYear(self):
        response = self.testapp.get("/events")
        self.assertEqual(response.status_int, 200)

    def testEventListExplicitYear(self):
        response = self.testapp.get("/events/2015")
        self.assertEqual(response.status_int, 200)

    def testEventListNoEvents(self):
        response = self.testapp.get("/events/2014")
        self.assertEqual(response.status_int, 200)

    def testEventDetails(self):
        response = self.testapp.get("/event/2016necmp")
        self.assertEqual(response.status_int, 200)

    def testEventDetailsNotFound(self):
        response = self.testapp.get("/event/2016meow", status=404)
        self.assertEqual(response.status_int, 404)

    def testEventInsights(self):
        response = self.testapp.get("/event/2016necmp/insights")
        self.assertEqual(response.status_int, 200)

    def testEventInsightsNotFound(self):
        response = self.testapp.get("/event/2016meow/insights", status=404)
        self.assertEqual(response.status_int, 404)
