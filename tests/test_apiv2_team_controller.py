import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from controllers.api.api_team_controller import ApiTeamController, ApiTeamEventsController

from consts.award_type import AwardType
from consts.event_type import EventType

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team


class TestTeamApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<team_key:>', ApiTeamController, methods=['GET'])], debug=True)
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

    def tearDown(self):
        self.testbed.deactivate()

    def assertTeamJson(self, team):
        self.assertEqual(team["key"], self.team.key_name)
        self.assertEqual(team["team_number"], self.team.team_number)
        self.assertEqual(team["nickname"], self.team.nickname)
        self.assertEqual(team["location"], self.team.location)
        self.assertEqual(team["locality"], "Greenville")
        self.assertEqual(team["country_name"], "USA")
        self.assertEqual(team["region"], "SC")
        self.assertEqual(team["website"], self.team.website)

    def testTeamApi(self):
        response = self.testapp.get('/frc281', headers={"X-TBA-App-Id": "tba-tests:team-controller-test:v01"})

        team_dict = json.loads(response.body)
        self.assertTeamJson(team_dict)


class TestTeamEventsApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<team_key:>/<year:>', ApiTeamEventsController, methods=['GET'])], debug=True)
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
                year=datetime.now().year,
                end_date=datetime(2010, 03, 27),
                official=True,
                location='Clemson, SC',
                start_date=datetime(2010, 03, 24),
        )
        self.event.put()

        self.event_team = EventTeam(
                team=self.team.key,
                event=self.event.key,
                year=2010
        )
        self.event_team.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertEventJson(self, event):
        self.assertEqual(event["key"], self.event.key_name)
        self.assertEqual(event["name"], self.event.name)
        self.assertEqual(event["short_name"], self.event.short_name)
        self.assertEqual(event["official"], self.event.official)
        self.assertEqual(event["start_date"], self.event.start_date.date().isoformat())
        self.assertEqual(event["end_date"], self.event.end_date.date().isoformat())
        self.assertEqual(event["event_type_string"], self.event.event_type_str)
        self.assertEqual(event["event_type"], self.event.event_type_enum)

    def testTeamApi(self):
        response = self.testapp.get('/frc281/2010', headers={"X-TBA-App-Id": "tba-tests:team-controller-test:v01"})

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict[0])
