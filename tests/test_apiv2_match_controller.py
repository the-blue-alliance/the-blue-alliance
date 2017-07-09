import unittest2
import webtest
import json
import webapp2
import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api.api_match_controller import ApiMatchController

from models.event import Event
from models.match import Match


class TestMatchApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<match_key:>', ApiMatchController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.match = Match(
            id="2014cc_f1m1",
            event=ndb.Key(Event, "2014cc"),
            year=2014,
            comp_level="f",
            set_number=1,
            match_number=1,
            team_key_names=[u'frc846', u'frc2135', u'frc971', u'254', u'frc1678', u'frc973'],
            time=datetime.datetime.fromtimestamp(1409527874),
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
        self.match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertMatchJson(self, match):
        self.assertEqual(str(match["key"]), self.match.key.string_id())
        self.assertEqual(match["comp_level"], self.match.comp_level)
        self.assertEqual(match["event_key"], self.match.event.string_id())
        self.assertEqual(match["set_number"], self.match.set_number)
        self.assertEqual(match["match_number"], self.match.match_number)
        self.assertEqual(match["alliances"], self.match.alliances)
        self.assertEqual(match["score_breakdown"], self.match.score_breakdown)
        self.assertEqual(match["videos"], self.match.videos)
        self.assertEqual(match["time_string"], self.match.time_string)
        if self.match.time is None:
            self.assertEqual(match["time"], None)
        else:
            self.assertEqual(match["time"], 1409527874)

    def test_match_api(self):
        response = self.testapp.get('/2014cc_f1m1', headers={"X-TBA-App-Id": "tba-tests:match-controller-test:v01"})

        match_json = json.loads(response.body)
        self.assertMatchJson(match_json)
