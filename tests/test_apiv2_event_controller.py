import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from controllers.api.api_event_controller import ApiEventController
from controllers.api.api_event_controller import ApiEventTeamsController
from controllers.api.api_event_controller import ApiEventMatchesController
from controllers.api.api_event_controller import ApiEventStatsController
from controllers.api.api_event_controller import ApiEventListController
from controllers.api.api_event_controller import ApiEventRankingsController

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class TestEventApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<event_key:>', ApiEventController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

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
                webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
                alliance_selections_json="[ {\"declines\": [], \"picks\": [\"frc971\", \"frc254\", \"frc1662\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc1678\", \"frc368\", \"frc4171\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc2035\", \"frc192\", \"frc4990\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc1323\", \"frc846\", \"frc2135\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc2144\", \"frc1388\", \"frc668\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc1280\", \"frc604\", \"frc100\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc114\", \"frc852\", \"frc841\"]},"+ 
                                           "{\"declines\": [], \"picks\": [\"frc2473\", \"frc3256\", \"frc1868\"]}]"
        )

        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertEventJson(self, event):
        self.assertEqual(event["key"], self.event.key_name)
        self.assertEqual(event["name"], self.event.name)
        self.assertEqual(event["short_name"], self.event.short_name)
        self.assertEqual(event["official"], self.event.official)
        self.assertEqual(event["start_date"], self.event.start_date.date().isoformat())
        self.assertEqual(event["end_date"], self.event.end_date.date().isoformat())
        self.assertEqual(event["webcast"], json.loads(self.event.webcast_json))
        self.assertEqual(event["alliances"], json.loads(self.event.alliance_selections_json))

    def testEventApi(self):
        response = self.testapp.get('/2010sc', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict)


class TestEventTeamsApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<event_key:>', ApiEventTeamsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

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

        self.event_team = EventTeam(
                team=self.team.key,
                event=self.event.key,
                year=datetime.now().year
        )
        self.event_team.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertTeamJson(self, team):
        team = team[0]
        self.assertEqual(team["key"], self.team.key_name)
        self.assertEqual(team["team_number"], self.team.team_number)
        self.assertEqual(team["nickname"], self.team.nickname)
        self.assertEqual(team["location"], self.team.location)
        self.assertEqual(team["locality"], "Greenville")
        self.assertEqual(team["country_name"], "USA")
        self.assertEqual(team["region"], "SC")
        self.assertEqual(team["website"], self.team.website)

    def testEventTeamsApi(self):
        response = self.testapp.get('/2010sc', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})

        team_dict = json.loads(response.body)
        self.assertTeamJson(team_dict)


class TestEventMatchApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<event_key:>', ApiEventMatchesController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

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

        self.match = Match(
            id="2010sc_qm1",
            alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc281", "frc571", "frc176"]}}""",
            comp_level="qm",
            event=self.event.key,
            game="frc_2012_rebr",
            set_number=1,
            match_number=1,
            team_key_names=[u'frc281', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
            youtube_videos=["94UGXIq6jUA"],
            tba_videos=[".mp4"]
        )
        self.match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertMatchJson(self, matches):
        match = matches[0]
        self.assertEqual(str(match["key"]), self.match.key.string_id())
        self.assertEqual(match["comp_level"], self.match.comp_level)
        self.assertEqual(match["event_key"], self.match.event.string_id())
        self.assertEqual(match["set_number"], self.match.set_number)
        self.assertEqual(match["match_number"], self.match.match_number)
        self.assertEqual(match["videos"], self.match.videos)
        self.assertEqual(match["time_string"], self.match.time_string)
        if self.match.time is None:
            self.assertEqual(match["time"], None)
        else:
            self.assertEqual(match["time"], self.match.time.strftime("%s"))
    
    def testEventMatchApi(self):
        response = self.testapp.get('/2010sc', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})

        match_json = json.loads(response.body)
        self.assertMatchJson(match_json)


class TestEventStatsApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<event_key:>', ApiEventStatsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        self.matchstats = {
            "dprs": {"971": 10.52178695299036, "114": 23.7313645955704, "115": 29.559784481082044},
            "oprs": {"971": 91.42946669932006, "114": 59.27751047482864, "115": 13.285278757495144},
            "ccwms": {"971": 80.90767974632955, "114": 35.54614587925829, "115": -16.27450572358693},
        }

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
                matchstats_json=json.dumps(self.matchstats)
        )
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testEventStatsApi(self):
        response = self.testapp.get('/2010sc', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})

        matchstats = json.loads(response.body)
        self.assertEqual(self.matchstats, matchstats)

class TestEventRankingsApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<event_key:>', ApiEventRankingsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        self.rankings = [
            ["Rank", "Team", "QS", "ASSIST", "AUTO", "T&C", "TELEOP", "Record (W-L-T)", "DQ", "PLAYED"], 
            ["1", "1126", "20.00", "240.00", "480.00", "230.00", "478.00", "10-2-0", "0", "12"], 
            ["2", "5030", "20.00", "200.00", "290.00", "220.00", "592.00", "10-2-0", "0", "12"], 
            ["3", "250", "20.00", "70.00", "415.00", "220.00", "352.00", "10-2-0", "0", "12"]
            ]
        

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
                rankings_json=json.dumps(self.rankings)
        )
        self.event.put()

        self.eventNoRanks = Event(
                id="2010ct",
                name="Palmetto Regional",
                event_type_enum=EventType.REGIONAL,
                short_name="Palmetto",
                event_short="ct",
                year=2010,
                end_date=datetime(2010, 03, 27),
                official=True,
                location='Clemson, SC',
                start_date=datetime(2010, 03, 24),
        )
        self.eventNoRanks.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testEventRankingsApi(self):
        response = self.testapp.get('/2010sc', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})

        rankings = json.loads(response.body)
        self.assertEqual(self.rankings, rankings)

    def testEventNoRankingsApi(self):
        response = self.testapp.get('/2010ct', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})

        self.assertEqual("[]", response.body)

class TestEventListApiController(unittest2.TestCase):

    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<year:>', ApiEventListController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

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

    def tearDown(self):
        self.testbed.deactivate()

    def assertEventJson(self, event):
        self.assertEqual(event["key"], self.event.key_name)
        self.assertEqual(event["name"], self.event.name)
        self.assertEqual(event["short_name"], self.event.short_name)
        self.assertEqual(event["official"], self.event.official)
        self.assertEqual(event["start_date"], self.event.start_date.date().isoformat())
        self.assertEqual(event["end_date"], self.event.end_date.date().isoformat())

    def testEventListApi(self):
        response = self.testapp.get('/2010', headers={"X-TBA-App-Id": "tba-tests:event-controller-test:v01"})
        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict[0])
