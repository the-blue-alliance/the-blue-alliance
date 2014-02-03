import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from controllers.api_controller import ApiTeamDetails, ApiTeamsShow

from models.team import Team
from models.event import Event
from models.event_team import EventTeam


class TestApiTeamShow(unittest2.TestCase):

    # TODO: Add event_keys testing. -brandondean 10/21/2012
    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiTeamsShow)], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        self.team = Team(
                id="frc281",
                name="Michelin / Caterpillar / Greenville Technical College /\
                jcpenney / Baldor / ASME / Gastroenterology Associates /\
                Laserflex South & Greenville County Schools & Greenville\
                Technical Charter High School",
                team_number=281,
                nickname="EnTech GreenVillians",
                address="Greenville, SC, USA",
                website="www.entech.org",
        )

        self.team.put()

        self.event = Event(
                id="2010sc",
                name="Palmetto Regional",
                event_type_enum=EventType.REGIONAL,
                short_name="Palmetto",
                event_short="sc",
                year=2010,
                end_date=datetime(2010, 03, 27),
                official=True,
                location='Clemson, SC',
                start_date=datetime(2010, 03, 24),
        )

        self.event.put()

        self.event_team = EventTeam(
                team=self.team.key,
                event=self.event.key,
                year=datetime.now().year
        )

        self.event_team.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertTeamJson(self, team_dict):
        self.assertEqual(team_dict["key"], self.team.key_name)
        self.assertEqual(team_dict["team_number"], self.team.team_number)
        self.assertEqual(team_dict["nickname"], self.team.nickname)
        self.assertEqual(team_dict["location"], self.team.location)
        self.assertEqual(team_dict["locality"], "Greenville")
        self.assertEqual(team_dict["country_name"], "USA")
        self.assertEqual(team_dict["region"], "SC")
        self.assertEqual(team_dict["website"], self.team.website)
        self.assertTrue(self.event.key.id() in team_dict["events"])

    def testTeamShow(self):
        response = self.testapp.get('/?teams=frc281', headers={"X-TBA-App-Id": "tba-tests:team-api-test:v01"})

        team_dict = json.loads(response.body)
        self.assertTeamJson(team_dict[0])

    def testNonexistentTeam(self):
        response = self.testapp.get('/?teams=frc3141579265', headers={"X-TBA-App-Id": "tba-tests:team-api-test:v01"}, status=404)

        self.assertEqual(response.status_int, 404)

    def test_validate_tba_app_id(self):
        response = self.testapp.get('/?teams=frc254', expect_errors=True)  # By default get() doesn't send a user agent
        self.assertEqual(response.status, "400 Bad Request")
        self.assertEqual(response.body, '{"Error": "X-TBA-App-Id is a required header."}')


class TestApiTeamDetails(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiTeamDetails)], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testNonexistentTeam(self):
        response = self.testapp.get('/?team=frc3141579265', headers={"X-TBA-App-Id": "tba-tests:team-api-test:v01"}, status=404)

        self.assertEqual(response.status_int, 404)

    def test_validate_tba_app_id(self):
        response = self.testapp.get('/?team=frc3141579265', expect_errors=True)  # By default get() doesn't send a user agent
        self.assertEqual(response.status, "400 Bad Request")
        self.assertEqual(response.body, '{"Error": "X-TBA-App-Id is a required header."}')
