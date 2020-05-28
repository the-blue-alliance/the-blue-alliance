import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from controllers.api.api_district_controller import ApiDistrictTeamsController
from controllers.api.api_team_controller import ApiTeamController, ApiTeamEventsController, ApiTeamMediaController,\
                                                ApiTeamListController, ApiTeamHistoryRobotsController,\
                                                ApiTeamHistoryDistrictsController

from models.district import District
from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.media import Media
from models.robot import Robot
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
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team = Team(
            id="frc281",
            name="Michelin / Caterpillar / Greenville Technical College /\
            jcpenney / Baldor / ASME / Gastroenterology Associates /\
            Laserflex South & Greenville County Schools & Greenville\
            Technical Charter High School",
            team_number=281,
            rookie_year=1999,
            nickname="EnTech GreenVillians",
            city="Greenville",
            state_prov="SC",
            country="USA",
            website="www.entech.org",
            motto="Infiltrating Young Minds One Robot at a Time"
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
        self.assertEqual(team["rookie_year"], self.team.rookie_year)
        self.assertEqual(team["motto"], None)

    def test_team_api(self):
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
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team = Team(
            id="frc281",
            name="Michelin / Caterpillar / Greenville Technical College /\
            jcpenney / Baldor / ASME / Gastroenterology Associates /\
            Laserflex South & Greenville County Schools & Greenville\
            Technical Charter High School",
            team_number=281,
            nickname="EnTech GreenVillians",
            city="Greenville",
            state_prov="SC",
            country="USA",
            website="www.entech.org"
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
            city='Clemson',
            state_prov='SC',
            country='USA',
            start_date=datetime(2010, 03, 24)
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

    def test_team_api(self):
        response = self.testapp.get('/frc281/2010', headers={"X-TBA-App-Id": "tba-tests:team-controller-test:v01"})

        event_dict = json.loads(response.body)
        self.assertEventJson(event_dict[0])


class TestDistrictTeamsApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<district_abbrev:>/<year:([0-9]*)>', ApiDistrictTeamsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team = Team(
            id="frc281",
            name="Michelin / Caterpillar / Greenville Technical College /\
            jcpenney / Baldor / ASME / Gastroenterology Associates /\
            Laserflex South & Greenville County Schools & Greenville\
            Technical Charter High School",
            team_number=281,
            nickname="EnTech GreenVillians",
            city="Greenville",
            state_prov="SC",
            country="USA",
            website="www.entech.org",
            motto="Infiltrating Young Minds One Robot at a Time"
        )

        self.district = District(
            id='2015ne',
            year=2015,
            abbreviation='ne'
        )

        self.district_team = DistrictTeam(
            id="2015ne_frc281",
            team=self.team.key,
            year=2015,
            district_key=ndb.Key(District, '2015ne')
        )

        self.team.put()
        self.district.put()
        self.district_team.put()

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
        self.assertEqual(team["motto"], None)

    def test_districts_api(self):
        response = self.testapp.get('/ne/2015', headers={"X-TBA-App-Id": "tba-tests:team-districts-controller-test:v01"})
        teams = json.loads(response.body)
        self.assertTeamJson(teams)


class TestTeamMediaApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<team_key:>/<year:>', ApiTeamMediaController, methods=['GET'])], debug=True)

        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team = Team(
            id="frc254",
            name="very long name",
            team_number=254,
            nickname="Teh Chezy Pofs",
            city="Greenville",
            state_prov="SC",
            country="USA"
        )
        self.team.put()

        self.cdmedia = Media(
            key=ndb.Key('Media', 'cdphotothread_39894'),
            details_json=u'{"image_partial": "fe3/fe38d320428adf4f51ac969efb3db32c_l.jpg"}',
            foreign_key=u'39894',
            media_type_enum=1,
            references=[ndb.Key('Team', 'frc254')],
            year=2014
        )
        self.cdmedia.put()
        self.cddetails = dict()
        self.cddetails["image_partial"] = "fe3/fe38d320428adf4f51ac969efb3db32c_l.jpg"

        self.ytmedia = Media(
            key=ndb.Key('Media', 'youtube_aFZy8iibMD0'),
            details_json=None,
            foreign_key=u'aFZy8iibMD0',
            media_type_enum=0,
            references=[ndb.Key('Team', 'frc254')],
            year=2014
        )
        self.ytmedia.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testTeamMediaApi(self):
        response = self.testapp.get('/frc254/2014', headers={"X-TBA-App-Id": "tba-tests:team_media-controller-test:v01"})
        media = json.loads(response.body)

        self.assertEqual(len(media), 2)

        cd = media[0]
        self.assertEqual(cd["type"], "cdphotothread")
        self.assertEqual(cd["foreign_key"], "39894")
        self.assertEqual(cd["details"], self.cddetails)

        yt = media[1]
        self.assertEqual(yt["type"], "youtube")
        self.assertEqual(yt["foreign_key"], "aFZy8iibMD0")
        self.assertEqual(yt["details"], {})


class TestTeamListApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<page_num:([0-9]*)>', ApiTeamListController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team1 = Team(
            id="frc123",
            name="SomeName",
            team_number=123,
            nickname="SomeNickname",
            city="San Jose",
            state_prov="CA",
            country="USA",
            website="www.website.com"
        )

        self.team2 = Team(
            id="frc4567",
            name="SomeName",
            team_number=4567,
            nickname="SomeNickname",
            city="San Jose",
            state_prov="CA",
            country="USA",
            website="www.website.com"
        )

        self.team1.put()
        self.team2.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertTeam1Json(self, team):
        self.assertEqual(team["key"], self.team1.key_name)
        self.assertEqual(team["name"], self.team1.name)
        self.assertEqual(team["team_number"], self.team1.team_number)

    def assertTeam2Json(self, team):
        self.assertEqual(team["key"], self.team2.key_name)
        self.assertEqual(team["name"], self.team2.name)
        self.assertEqual(team["team_number"], self.team2.team_number)

    def testTeamListApi(self):
        response = self.testapp.get('/0', headers={"X-TBA-App-Id": "tba-tests:team_list-controller-test:v01"})
        team_list = json.loads(response.body)
        self.assertTeam1Json(team_list[0])

        response = self.testapp.get('/9', headers={"X-TBA-App-Id": "tba-tests:team_list-controller-test:v01"})
        team_list = json.loads(response.body)
        self.assertTeam2Json(team_list[0])

        response = self.testapp.get('/10', headers={"X-TBA-App-Id": "tba-tests:team_list-controller-test:v01"})
        team_list = json.loads(response.body)
        self.assertEqual(team_list, [])


class TestTeamHistoryRobotsApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<team_key:>', ApiTeamHistoryRobotsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team = Team(
            id="frc1124",
            name="UberBots",
            team_number=1124,
            nickname="UberBots"
        )

        self.robot = Robot(
            id="frc1124_2015",
            team=self.team.key,
            year=2015,
            robot_name="Orion"
        )

        self.team.put()
        self.robot.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testRobotApi(self):
        response = self.testapp.get('/frc1124', headers={"X-TBA-App-Id": "tba-tests:team_list-controller-test:v01"})
        robot_dict = json.loads(response.body)

        self.assertTrue("2015" in robot_dict)
        robot = robot_dict["2015"]

        self.assertEqual(robot["key"], "frc1124_2015")
        self.assertEqual(robot["team_key"], "frc1124")
        self.assertEqual(robot["year"], 2015)
        self.assertEqual(robot["name"], "Orion")


class TestTeamHistoryDistrictsApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<team_key:>', ApiTeamHistoryDistrictsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.team = Team(
            id="frc1124",
            name="UberBots",
            team_number=1124,
            nickname="UberBots"
        )

        self.district_team = DistrictTeam(
            id="2015ne_frc1124",
            team=self.team.key,
            year=2015,
            district_key=ndb.Key(District, '2015ne')
        )

        self.district = District(
            id='2015ne',
            year=2015
        )

        self.team.put()
        self.district_team.put()
        self.district.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testDistrictsApi(self):
        response = self.testapp.get('/frc1124', headers={"X-TBA-App-Id": "tba-tests:team-history-districts-controller-test:v01"})
        district_dict = json.loads(response.body)

        self.assertTrue("2015" in district_dict)
        district_key = district_dict["2015"]

        self.assertEqual(district_key, "2015ne")
