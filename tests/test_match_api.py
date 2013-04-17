import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api_controller import ApiMatchDetails

from models.event import Event
from models.match import Match

class TestApiMatchDetails(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiMatchDetails)], debug=True)
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
        self.assertEqual(match_dict["alliances"], json.loads(self.match.alliances_json))
        self.assertEqual(match_dict["team_keys"], self.match.team_key_names)
        self.assertEqual(match_dict["event"], self.event.key_name)
        self.assertEqual(match_dict["game"], self.match.game)
        self.assertEqual(match_dict["comp_level"], self.match.comp_level)
        self.assertEqual(match_dict["set_number"], self.match.set_number)
        self.assertEqual(match_dict["match_number"], self.match.match_number)

    def testMatchDetails(self):
        response = self.testapp.get("/?match=2010cmp_f1m1")

        match_dict = json.loads(response.body)
        self.assertMatch(match_dict)


class TestApiMatchDetailsList(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiMatchDetails)], debug=True)
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

        self.match2 = Match(
                id = '2010cmp_f1m2',
                comp_level = 'f',
                match_number = 1,
                team_key_names = match_team_key_names,
                alliances_json = self.match_json,
                set_number = 1,
                game = 'frc_2010_bkwy',
                event = self.event.key
        )
        self.match2.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertMatch(self, match_dict):
        self.assertEqual(match_dict[0]["key"], self.match.key_name)
        self.assertEqual(match_dict[0]["alliances"], json.loads(self.match.alliances_json))
        self.assertEqual(match_dict[0]["team_keys"], self.match.team_key_names)
        self.assertEqual(match_dict[0]["event"], self.event.key_name)
        self.assertEqual(match_dict[0]["game"], self.match.game)
        self.assertEqual(match_dict[0]["comp_level"], self.match.comp_level)
        self.assertEqual(match_dict[0]["set_number"], self.match.set_number)
        self.assertEqual(match_dict[0]["match_number"], self.match.match_number)

    def testMatchDetailsList(self):
        response = self.testapp.get("/?matches=2010cmp_f1m1,2010cmp_f1m2")

        match_dict = json.loads(response.body)
        self.assertMatch(match_dict)
