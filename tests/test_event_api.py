import json
import os
import unittest2
import webtest
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from controllers.api_controller import ApiEventsShow, ApiEventList, ApiMatchDetails

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
            id="2010sc",
            name="Palmetto Regional",
            event_type_enum=EventType.REGIONAL,
            short_name="Palmetto",
            event_short="sc",
            year=2010,
            end_date=datetime(2010, 03, 27),
            official=True,
            location='Clemson, SC',
            start_date=datetime(2010, 03, 24)
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

    def test_event_show(self):
        response = self.testapp.get('/?year=2010')

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict[0])


class TestApiMatchDetails(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([(r'/', ApiMatchDetails)], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()

        events = {
            '2010cmp': Event(
                id="2010cmp",
                name="Einstein Field",
                event_type_enum=EventType.CMP_FINALS,
                short_name="Einstein",
                event_short="cmp",
                year=2010,
                start_date=datetime(2010, 04, 17),
                end_date=datetime(2010, 04, 17),
                official=True,
                location='Atlanta, GA'
            ),
            '2011cmp': Event(
                id="2011cmp",
                name="Einstein Field",
                event_type_enum=EventType.CMP_FINALS,
                short_name="Einstein",
                event_short="cmp",
                year=2011,
                start_date=datetime(2011, 04, 30),
                end_date=datetime(2011, 04, 30),
                official=True,
                location='St. Louis, MO'
            ),
            '2012cmp': Event(
                id="2012cmp",
                name="Einstein Field",
                event_type_enum=EventType.CMP_FINALS,
                short_name="Einstein",
                event_short="cmp",
                year=2012,
                start_date=datetime(2012, 04, 26),
                end_date=datetime(2012, 04, 28),
                official=True,
                location='St. Louis, MO'
            )
        }

        event_keys = {}

        for event_id, event in events.items():
            event_keys[event_id] = event.put()

        self.matches = {
            '2010cmp_f1m1': Match(
                id='2010cmp_f1m1',
                comp_level='f',
                match_number=1,
                team_key_names=["frc177", "frc67", "frc294", "frc469", "frc1114", "frc2041"],
                alliances_json='{"blue": {"score": "14", "teams": ["frc469", "frc1114", "frc2041"]}, "red": {"score": "16", "teams": ["frc177", "frc67", "frc294"]}}',
                set_number=1,
                game='frc_2010_bkwy',
                event=event_keys['2010cmp']
            ),
            '2011cmp_f1m1': Match(
                id='2011cmp_f1m1',
                comp_level='f',
                match_number=1,
                team_key_names=["frc973", "frc254", "frc111", "frc177", "frc2016", "frc781"],
                alliances_json='{"blue": {"score": 79, "teams": ["frc177", "frc2016", "frc781"]}, "red": {"score": 147, "teams": ["frc973", "frc254", "frc111"]}}',
                set_number=1,
                game='frc_2011_logo',
                event=event_keys['2011cmp']
            ),
            '2012cmp_f1m1': Match(
                id='2012cmp_f1m1',
                comp_level='f',
                match_number=1,
                team_key_names=["frc25", "frc180", "frc16", "frc207", "frc233", "frc987"],
                alliances_json='{"blue": {"score": 45, "teams": ["frc207", "frc233", "frc987"]}, "red": {"score": 89, "teams": ["frc25", "frc180", "frc16"]}}',
                set_number=1,
                game='frc_2012_rebr',
                event=event_keys['2012cmp']
            )
        }

        for match in self.matches.values():
            match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertMatch(self, match):
        match_id = match["key"]

        self.assertEqual(match["event"], self.matches[match_id].event.get().key_name)
        self.assertEqual(match["competition_level"], self.matches[match_id].name)
        self.assertEqual(match["set_number"], self.matches[match_id].set_number)
        self.assertEqual(match["match_number"], self.matches[match_id].match_number)
        self.assertEqual(match["team_keys"], self.matches[match_id].team_key_names)

        # FIXME: urgh. strings. - brandondean 10/21/2012
        #self.assertEqual(match["alliances"], self.matches[match_id].alliances_json)

    def assertMatchNames(self, match_list):
        match_names = ",".join(match_list)
        api_names = ["match", "matches"]

        for api_name in api_names:
            response = self.testapp.get("/?" + api_name + "=" + match_names)

            matches = json.loads(response.body)
            for match in matches:
                match["alliances"] = str(match["alliances"])
                self.assertIn(match["key"], self.matches)
                self.assertMatch(match)

    def test_match_details(self):
        self.assertMatchNames(["2010cmp_f1m1"])
        self.assertMatchNames(["2010cmp_f1m1", "2011cmp_f1m1", "2012cmp_f1m1"])
