import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from controllers.api.api_team_controller import ApiTeamController, ApiTeamMediaController

from consts.award_type import AwardType
from consts.event_type import EventType

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
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
        self.testbed.init_taskqueue_stub()

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

    def testTeamApi(self):
        response = self.testapp.get('/frc281', headers={"X-TBA-App-Id": "tba-tests:team-controller-test:v01"})

        team_dict = json.loads(response.body)
        self.assertTeamJson(team_dict)


class TestTeamMediaApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<team_key:>/<year:>', ApiTeamMediaController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        self.team = Team(
                id="frc254",
                name="very long name",
                team_number=254,
                nickname="Teh Chezy Pofs",
                address="Greenville, SC, USA"
        )
        self.team.put()

        self.cdmedia = Media(
                        key=ndb.Key('Media', 'cdphotothread_39894'),
                        details_json=u'{"image_partial": "fe3/fe38d320428adf4f51ac969efb3db32c_l.jpg"}',
                        foreign_key=u'39894',
                        media_type_enum=1,
                        references=[ndb.Key('Team', 'frc254')],
                        year=2014)
        self.cdmedia.put()
        self.cddetails = dict()
        self.cddetails["image_partial"] = "fe3/fe38d320428adf4f51ac969efb3db32c_l.jpg"

        self.ytmedia = Media(
                        key=ndb.Key('Media', 'youtube_aFZy8iibMD0'),
                        details_json=None,
                        foreign_key=u'aFZy8iibMD0',
                        media_type_enum=0,
                        references=[ndb.Key('Team', 'frc254')],
                        year=2014)
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
