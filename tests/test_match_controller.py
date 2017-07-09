from datetime import datetime

import unittest2
import webapp2
import webtest
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.event_type import EventType
from controllers.match_controller import MatchDetail
from models.event import Event
from models.match import Match


class TestMatchController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/match/<match_key>', MatchDetail, 'match-detail'),
        ])
        self.testapp = webtest.TestApp(app)

        self.match = Match(
            id="2014cc_f1m1",
            event=ndb.Key(Event, "2014cc"),
            year=2014,
            comp_level="f",
            set_number=1,
            match_number=1,
            team_key_names=[u'frc846', u'frc2135', u'frc971', u'254', u'frc1678', u'frc973'],
            time=datetime.fromtimestamp(1409527874),
            time_string="4:31 PM",
            youtube_videos=["JbwUzl3W9ug", "bHGyTjxbLz8"],
            tba_videos=[],
            alliances_json='{\
                "blue": {\
                    "score": 270,\
                    "teams": [\
                    "frc846",\
                    "frc2135",\
                    "frc971"]},\
                "red": {\
                    "score": 310,\
                    "teams": [\
                    "frc254",\
                    "frc1678",\
                    "frc973"]}}',
            score_breakdown_json='{\
                "blue": {\
                    "auto": 70,\
                    "teleop_goal+foul": 40,\
                    "assist": 120,\
                    "truss+catch": 40\
                },"red": {\
                    "auto": 70,\
                    "teleop_goal+foul": 50,\
                    "assist": 150,\
                    "truss+catch": 40}}'
        )
        self.event = Event(
            id="2014cc",
            name="Cheesy Champs",
            event_type_enum=EventType.OFFSEASON,
            short_name="Cheesy Champs",
            event_short="cc",
            year=2014,
            end_date=datetime(2014, 03, 27),
            official=True,
            city='Hartford',
            state_prov='CT',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2014, 03, 24)
        )
        self.match.put()
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_match_detail(self):
        response = self.testapp.get("/match/2014cc_f1m1")
        self.assertEqual(response.status_int, 200)

    def test_bad_match_detail(self):
        response = self.testapp.get("/match/2014cc_f1m2", status=404)
        self.assertEqual(response.status_int, 404)
