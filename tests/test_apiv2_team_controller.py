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

        self.event = Event(
                id="2010sc",
                name="Palmetto Regional",
                event_type_enum=EventType.REGIONAL,
                short_name="Palmetto",
                event_short="sc",
                year=datetime.now().year,
                end_date=datetime(2010, 03, 27),
                official=True,
                location='Clemson, SC',
                start_date=datetime(2010, 03, 24),
        )

        self.event.put()

        self.event_team = EventTeam(
                team=self.team.key,
                event=self.event.key,
                year=datetime.now().year
        )
        self.event_team.put()

        self.match = Match(
            id="2010sc_qm1",
            alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc281", "frc571", "frc176"]}}""",
            comp_level="qm",
            event=self.event.key,
            game="frc_2012_rebr",
            set_number=1,
            match_number=1,
            team_key_names=[u'frc281', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],

        )
        self.match.put()

        self.award = Award(
            name_str = "Engineering Inspiration",
            award_type_enum = AwardType.ENGINEERING_INSPIRATION,
            year=datetime.now().year,
            event = self.event.key,
            event_type_enum = EventType.REGIONAL,
            team_list = [self.team.key],
            recipient_json_list=[json.dumps({'team_number': 281, 'awardee': None})],
        )
        self.award.put()

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

    def assertEventJson(self, event):
        self.assertEqual(event["key"], self.event.key_name)
        self.assertEqual(event["name"], self.event.name)
        self.assertEqual(event["short_name"], self.event.short_name)
        self.assertEqual(event["official"], self.event.official)
        self.assertEqual(event["start_date"], self.event.start_date.date().isoformat())
        self.assertEqual(event["end_date"], self.event.end_date.date().isoformat())
        self.assertEqual(event["event_type_string"], self.event.event_type_str)
        self.assertEqual(event["event_type"], self.event.event_type_enum)

    def assertMatchJson(self, match):
        self.assertEqual(str(match["key"]), self.match.key.string_id())
        self.assertEqual(match["comp_level"], self.match.comp_level)
        self.assertEqual(match["event_key"], self.match.event.string_id())
        self.assertEqual(match["set_number"], self.match.set_number)
        self.assertEqual(match["match_number"], self.match.match_number)

    def assertAwardJson(self, award):
        self.assertEqual(award["name"], self.award.name_str)
        self.assertEqual(award["event_key"], self.award.event.string_id())
        self.assertEqual(award["recipient_list"], self.award.recipient_list)
        self.assertEqual(award["year"], self.award.year)

    def testTeamApi(self):
        response = self.testapp.get('/frc281', headers={"X-TBA-App-Id": "tba-tests:team-controller-test:v01"})

        team_dict = json.loads(response.body)
        self.assertTeamJson(team_dict)
        self.assertEventJson(team_dict["events"][0])
        self.assertMatchJson(team_dict["events"][0]["matches"][0])
        self.assertAwardJson(team_dict["events"][0]["awards"][0])

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
