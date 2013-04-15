import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api_controller import ApiEventsShow, ApiEventList,\
                                       ApiMatchDetails, ApiEventDetails

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class TestApiEventList(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiEventList)], debug=True)
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


    def tearDown(self):
        self.testbed.deactivate()

    def assertEventJson(self, event_dict):
        self.assertEqual(event_dict["key"], self.event.key_name)
        self.assertEqual(event_dict["name"], self.event.name)
        self.assertEqual(event_dict["short_name"], self.event.short_name)
        self.assertEqual(event_dict["official"], self.event.official)
        self.assertEqual(event_dict["start_date"], self.event.start_date.isoformat())
        self.assertEqual(event_dict["end_date"], self.event.end_date.isoformat())

    def testEventShow(self):
        response = self.testapp.get('/?year=2010')

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict[0])


class TestApiEventDetails(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiEventDetails)], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

        self.year = datetime.now().year
        self.team = Team(
                id = "frc281",
                name = "Michelin / Caterpillar / Greenville Technical College /\
                jcpenney / Baldor / ASME / Gastroenterology Associates /\
                Laserflex South & Greenville County Schools & Greenville\
                Technical Charter High School",
                team_number = 281,
                nickname = "EnTech GreenVillians",
                address = "Greenville, SC, USA",
                website = "www.entech.org",
        )

        self.team.put()

        self.event = Event(
                id = "%ssc" % self.year,
                name = "Palmetto Regional",
                event_type = "Regional",
                short_name = "Palmetto",
                event_short = "sc",
                year = self.year,
                end_date = datetime(2010, 03, 27),
                official = True,
                location = 'Clemson, SC',
                start_date = datetime(2010, 03, 24),
        )

        self.event.put()

        self.event_team = EventTeam(
                team = self.team.key,
                event = self.event.key,
                year = self.year
        )

        self.event_team.put()

        self.match = Match(
            id = "%ssc_qm1" % self.year,
            alliances_json = """{"blue": {"score": 57, "teams": ["frc3464", "frc281", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
            comp_level = "qm",
            event = self.event.key,
            game = Match.FRC_GAMES_BY_YEAR[self.year],
            set_number = 1,
            match_number = 1,
            team_key_names = [u'frc69', u'frc571', u'frc176', u'frc3464', u'frc281', u'frc1073']
        )

        self.match.put()

        self.award = Award(
            id = "%ssc_rca" % self.year,
            name = "rca",
            official_name = "Regional Chairman's Award",
            team = self.team.key,
            awardee = "Dean Kamen",
            event = self.event.key,
            year = self.year
        )

        self.award.put()


    def tearDown(self):
        self.testbed.deactivate()

    def assertEventJson(self, event_dict):
        self.assertEqual(event_dict["key"], self.event.key_name)
        self.assertEqual(event_dict["name"], self.event.name)
        self.assertEqual(event_dict["short_name"], self.event.short_name)
        self.assertEqual(event_dict["event_code"], self.event.event_short)
        self.assertEqual(event_dict["event_type"], self.event.event_type)
        self.assertEqual(event_dict["year"], self.event.year)
        self.assertEqual(event_dict["start_date"], self.event.start_date.isoformat())
        self.assertEqual(event_dict["end_date"], self.event.end_date.isoformat())
        self.assertEqual(event_dict["official"], self.event.official)
        self.assertEqual(event_dict["location"], self.event.location)

        team = event_dict["teams"][0]
        self.assertEqual(team["key"], self.team.key_name)
        self.assertEqual(team["team_number"], self.team.team_number)
        self.assertEqual(team["nickname"], self.team.nickname)
        self.assertEqual(team["location"], self.team.location)
        self.assertEqual(team["locality"], "Greenville")
        self.assertEqual(team["country_name"], "USA")
        self.assertEqual(team["region"], "SC")
        self.assertEqual(team["website"], self.team.website)

        match = event_dict["matches"][0]
        self.assertEqual(match["key"], self.match.key_name)
        self.assertEqual(match["alliances"], json.loads(self.match.alliances_json))
        self.assertEqual(match["team_keys"], self.match.team_key_names)
        self.assertEqual(match["event"], self.event.key_name)
        self.assertEqual(match["game"], self.match.game)
        self.assertEqual(match["comp_level"], self.match.comp_level)
        self.assertEqual(match["set_number"], self.match.set_number)
        self.assertEqual(match["match_number"], self.match.match_number)

        award = event_dict["awards"][0]
        self.assertEqual(award["key"], self.award.key_name)
        self.assertEqual(award["name"], self.award.name)
        self.assertEqual(award["official_name"], self.award.official_name)
        self.assertEqual(award["year"], self.award.year)
        self.assertEqual(award["team"], self.team.key_name)
        self.assertEqual(award["awardee"], self.award.awardee)
        self.assertEqual(award["event"], self.event.key_name)


    def testEventDetails(self):
        response = self.testapp.get("/?event=%ssc" % self.year)

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict)

