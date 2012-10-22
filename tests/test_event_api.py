import unittest2
import webtest
import json
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api_controller import ApiEventsShow

from models.event import Event
from models.team import Team
from models.event_team import EventTeam

class TestApiEventShow(unittest2.TestCase):

    def setUp(self):
        app = webapp.WSGIApplication([(r'/', ApiEventsShow)], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

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


        self.event.put()
        self.team.put()

        self.event_team = EventTeam(
                team = self.team.key,
                event = self.event.key,
                year = 2010
        )

        self.event_team.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertEventJson(self, event_dict):
        self.assertEqual(event_dict["key"], self.event.key_name)
        self.assertEqual(event_dict["end_date"], self.event.end_date.isoformat())
        self.assertEqual(event_dict["name"], self.event.name)
        self.assertEqual(event_dict["short_name"], self.event.short_name)
        self.assertEqual(event_dict["facebook_eid"], self.event.facebook_eid)
        self.assertEqual(event_dict["official"], self.event.official)
        self.assertEqual(event_dict["location"], self.event.location)
        self.assertEqual(event_dict["event_code"], self.event.event_short)
        self.assertEqual(event_dict["year"], self.event.year)
        self.assertEqual(event_dict["start_date"], self.event.start_date.isoformat())
        self.assertEqual(event_dict["teams"][0], self.team.key_name)

    def testEventShow(self):
        response = self.testapp.get('/?events=2010sc')

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict[0])

