import unittest2
import webtest
import json
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api_controller import ApiEventsShow, ApiMatchDetails

from models.event import Event
from models.team import Team
from models.match import Match
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

class TestApiMatchDetails(unittest2.TestCase):

    def setUp(self):
        app = webapp.WSGIApplication([(r'/', ApiMatchDetails)], debug=True)
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
        self.event.put()

        self.match_json = '{"blue": {"score": "14", "teams": ["frc469", "frc1114", "frc2041"]}, "red": {"score": "16", "teams": ["frc177", "frc67", "frc294"]}}'
        match_team_key_names = ["frc177", "frc67", "frc294", "frc469", "frc1114", "frc2041"]

        self.match = Match(
                id = '2010cmp_f1m1',
                comp_level = 'f',
                match_number = 1,
                team_key_names = match_team_key_names,
                alliances_json = self.match_json,
                set_number = 1,
                game = 'frc_2010_bkwy',
                event = self.event.key
        )
        self.match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertMatch(self, match_dict):
        self.assertEqual(match_dict["key"], self.match.key_name)
        self.assertEqual(match_dict["event"], self.event.key_name)
        self.assertEqual(match_dict["comp_level"], self.match.name)
        self.assertEqual(match_dict["set_number"], self.match.set_number)
        self.assertEqual(match_dict["match_number"], self.match.match_number)
        self.assertEqual(match_dict["team_keys"], self.match.team_key_names)

        #FIXME: urgh. strings. - brandondean 10/21/2012
        #self.assertEqual(match_dict["alliances"], self.match_json)


    def testMatchDetails(self):
        response = self.testapp.get("/?match=2010cmp_f1m1")

        match_dict = json.loads(response.body)
        match_dict["alliances"] = str(match_dict["alliances"])
        self.assertMatch(match_dict)
