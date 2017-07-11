from datetime import datetime

import unittest2
import webapp2
import webtest
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.event_type import EventType
from controllers.team_controller import TeamList, TeamHistory, TeamDetail, TeamCanonical
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class TestTeamController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/team/<team_number:[0-9]+>', TeamCanonical, 'team-canonical'),
            RedirectRoute(r'/team/<team_number:[0-9]+>/<year:[0-9]+>', TeamDetail, 'team-detail'),
            RedirectRoute(r'/team/<team_number:[0-9]+>/history', TeamHistory, 'team-history'),
            RedirectRoute(r'/teams/<page:[0-9]+>', TeamList, 'team-list-year'),
            RedirectRoute(r'/teams', TeamList, 'team-list'),
        ])
        self.testapp = webtest.TestApp(app)

        self.team = Team(
            id="frc1124",
            name="Really Long Name",
            team_number=1124,
            rookie_year=2003,
            nickname="The UberBots",
            city="Avon",
            state_prov="CT",
            country="USA",
            website="www.uberbots.org",
            motto="This is a motto"
        )
        self.event = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
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
            start_date=datetime(2016, 03, 24)
        )
        self.event_team = EventTeam(
            id="2016necmp_frc1124",
            team=self.team.key,
            event=self.event.key,
            year=2016
        )
        self.event2 = Event(
            id="2015necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            short_name="New England",
            event_short="necmp",
            year=2015,
            end_date=datetime(2015, 03, 27),
            official=True,
            city='Hartford',
            state_prov='CT',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2015, 03, 24)
        )
        self.event_team2 = EventTeam(
            id="2015necmp_frc1124",
            team=self.team.key,
            event=self.event2.key,
            year=2015
        )
        self.event_team.put()
        self.team.put()
        self.event.put()
        self.event_team.put()
        self.event2.put()
        self.event_team2.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_team_list_default_page(self):
        response = self.testapp.get("/teams")
        self.assertEqual(response.status_int, 200)

    def test_team_list_explicit_page(self):
        response = self.testapp.get("/teams/1")
        self.assertEqual(response.status_int, 200)

    def test_team_list_bad_page(self):
        response = self.testapp.get("/teams/19", status=404)
        self.assertEqual(response.status_int, 404)

    def test_team_canonical(self):
        response = self.testapp.get("/team/1124")
        self.assertEqual(response.status_int, 200)

    def test_bad_team_canonical(self):
        response = self.testapp.get("/team/1337", status=404)
        self.assertEqual(response.status_int, 404)

    def test_team_detail(self):
        response = self.testapp.get("/team/1124/2016")
        self.assertEqual(response.status_int, 200)

    # Because 2015 is special :/
    def test_team_detail_2015(self):
        response = self.testapp.get("/team/1124/2015")
        self.assertEqual(response.status_int, 200)

    def test_team_detail_bad_year(self):
        response = self.testapp.get("/team/1124/2014", status=404)
        self.assertEqual(response.status_int, 404)

    def test_bad_team_detail(self):
        response = self.testapp.get("/team/1337/2016", status=404)
        self.assertEqual(response.status_int, 404)

    def test_team_history(self):
        response = self.testapp.get("/team/1124/history")
        self.assertEqual(response.status_int, 200)

    def test_bad_team_history(self):
        response = self.testapp.get("/team/1337/history", status=404)
        self.assertEqual(response.status_int, 404)
