import unittest2
import webtest
import json

from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api_controller import ApiTeamsShow

from models.team import Team
from models.event import Event
from models.event_team import EventTeam

class TestApiTeamShow(unittest2.TestCase):

    #TODO: Add event_keys testing. -brandondean 10/21/2012
    def setUp(self):
        app = webapp.WSGIApplication([(r'/', ApiTeamsShow)], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

        self.team = Team(
                id = "frc281",
                name = "Michelin / Caterpillar / Greenville Technical College /\
                jcpenney / Baldor / ASME / Gastroenterology Associates /\
                Laserflex South & Greenville County Schools & Greenville\
                Technical Charter High School",
                team_number = 281,
                nickname = "EnTech GreenVillians",
                address = "Greenville, SC",
                website = "www.entech.org",
        )

        self.team.put()

        self.event = Event(
                id = "2010sc",
                name = "Palmetto Regional",
                event_type = "Regional",
                short_name = "Palmetto",
                event_short = "sc",
                year = 2010,
                end_date = datetime(2010, 03, 27),
                official = True,
                location = 'Clemson, SC',
                start_date = datetime(2010, 03, 24),
        )

        self.event.put()

        self.event_team = EventTeam(
                team = self.team.key,
                event = self.event.key,
                year = datetime.now().year
        )

        self.event_team.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertTeamJson(self, team_dict):
        self.assertEqual(team_dict["key"], self.team.key_name)
        self.assertEqual(team_dict["team_number"], self.team.team_number)
        self.assertEqual(team_dict["nickname"], self.team.nickname)
        self.assertEqual(team_dict["location"], self.team.address)
        self.assertEqual(team_dict["country"], None)
        self.assertEqual(team_dict["region"], '')
        self.assertEqual(team_dict["website"], self.team.website)
        self.assertEqual(team_dict["events"][0], self.event.key_name)

    def testTeamShow(self):
        response = self.testapp.get('/?teams=frc281')

        team_dict = json.loads(response.body)
        self.assertTeamJson(team_dict[0])
