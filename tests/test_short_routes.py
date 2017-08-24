import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.event_type import EventType
from controllers.event_controller import EventDetail
from controllers.team_controller import TeamCanonical
from controllers.short_controller import ShortEventHandler, ShortTeamHandler
from models.team import Team
from models.event import Event


class TestShortController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r"/team/<team_number:[0-9]+>", TeamCanonical, "team-canonical"),
            RedirectRoute(r"/event/<event_key>", EventDetail, "event-detail"),
            RedirectRoute(r"/<:(frc)?><team_number:[0-9]+>", ShortTeamHandler, "short-team-canonical"),
            RedirectRoute(r"/<event_key:[0-9]{4}[a-z0-9]+>", ShortEventHandler, "short-event-detail"),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

        self.team1 = Team(
            id="frc1",
            team_number=1,
        )
        self.team2 = Team(
            id="frc16",
            team_number=16,
        )
        self.team3 = Team(
            id="frc254",
            team_number=254,
        )
        self.team4 = Team(
            id="frc2521",
            team_number=2521,
        )

        self.event1 = Event(
            id="2017necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            short_name="New England",
            event_short="necmp",
            year=2017,
            end_date=datetime(2017, 03, 27),
            official=True,
            city="Hartford",
            state_prov="CT",
            country="USA",
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2017, 03, 24),
            webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
            website="http://www.firstsv.org"
        )

        self.event2 = Event(
            id="2017mndu2",
            name="Northern Lights Regional",
            event_type_enum=EventType.REGIONAL,
            short_name="Northern Lights",
            event_short="mndu2",
            year=2017,
            end_date=datetime(2017, 03, 04),
            official=True,
            city="Duluth",
            state_prov="MN",
            country="USA",
            venue="Duluth Entertainment Convention Center",
            venue_address="Duluth Entertainment Convention Center, Duluth, MN, USA",
            timezone_id="America/New_York",
            start_date=datetime(2017, 03, 1),
            webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
            website="http://www.mnfirst.org"
        )

        self.team1.put()
        self.team2.put()
        self.team3.put()
        self.team4.put()
        self.event1.put()
        self.event2.put()

    def test_team_redirect(self):
        # 1 digit team
        response = self.testapp.get("/1", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/1")

        response = self.testapp.get("/frc1", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/1")

        # 2 digit team
        response = self.testapp.get("/16", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/16")

        response = self.testapp.get("/frc16", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/16")

        # 3 digit team
        response = self.testapp.get("/254", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/254")

        response = self.testapp.get("/frc254", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/254")

        # 4 digit team
        response = self.testapp.get("/2521", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/2521")

        response = self.testapp.get("/frc2521", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/team/2521")

    def test_event_redirect(self):
        # Normal event code
        response = self.testapp.get("/2017necmp", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/event/2017necmp")

        # Event code with numbers
        response = self.testapp.get("/2017mndu2", status="3*")
        response = response.follow()
        self.assertEqual(response.request.path, "/event/2017mndu2")

        # Non-existing event code
        response = self.testapp.get("/2017meow", status="3*")
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, "/event/2017meow")
        self.assertEqual(response.status_int, 404)

    def test_no_redirect(self):
        # Teams

        # Negative team number
        response = self.testapp.get("/-2521", status=404)
        self.assertEqual(response.status_int, 404)

        # Events

        # Semi-real year
        response = self.testapp.get("/217nytr", status=404)
        self.assertEqual(response.status_int, 404)
