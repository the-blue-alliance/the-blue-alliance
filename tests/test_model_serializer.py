import datetime
import json
import unittest2

from consts.event_type import EventType
from datafeeds.parsers.fms_api.fms_api_awards_parser import FMSAPIAwardsParser
from datafeeds.parsers.fms_api.fms_api_event_list_parser import FMSAPIEventListParser
from datafeeds.usfirst_event_rankings_parser import UsfirstEventRankingsParser
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from helpers.model_serializer import ModelSerializer
from models.award import Award
from models.event import Event
from models.event_details import EventDetails
from models.location import Location
from models.match import Match
from models.media import Media
from models.robot import Robot
from models.team import Team


class TestModelSerializer(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def _test_to_and_back(self, o):
        j = json.dumps(ModelSerializer.to_json(o), indent=2)
        self.assertEqual(o, ModelSerializer.to_obj(json.loads(j)))

    def test_award_conversion(self):
        event = Event(
            id="2015waamv",
            end_date=datetime.datetime(2015, 4, 2, 0, 0),
            event_short="waamv",
            event_type_enum=EventType.REGIONAL,
            district_key=None,
            first_eid="13467",
            name="PNW District - Auburn Mountainview Event",
            start_date=datetime.datetime(2015, 3, 31, 0, 0),
            year=2015,
            timezone_id='America/Los_Angeles'
        )
        with open('test_data/fms_api/2015waamv_staging_awards.json', 'r') as f:
            awards = FMSAPIAwardsParser(event).parse(json.loads(f.read()))
        event = Event(
            id="2017cmpmo",
            end_date=datetime.datetime(2017, 4, 29, 0, 0),
            event_short="cmpmo",
            event_type_enum=EventType.CMP_FINALS,
            district_key=None,
            first_eid="22465",
            name="Einstein Field (St. Louis)",
            start_date=datetime.datetime(2017, 4, 29, 0, 0),
            year=2017,
            timezone_id='America/Chicago'
        )
        with open('test_data/fms_api/2017cmpmo_awards.json', 'r') as f:
            awards += FMSAPIAwardsParser(event).parse(json.loads(f.read()))
        self._test_to_and_back(awards)

    def test_district_conversion(self):
        with open('test_data/fms_api/2017_event_list.json', 'r') as f:
            _, districts = FMSAPIEventListParser(2017).parse(json.loads(f.read()))
        self._test_to_and_back(districts)

    def test_event_conversion(self):
        with open('test_data/fms_api/2017_event_list.json', 'r') as f:
            events, _ = FMSAPIEventListParser(2017).parse(json.loads(f.read()))
        events.append(Event(
            id='2017casj',
            year=2017,
            city='San Jose',
            state_prov='CA',
            country='USA',
            postalcode='95112',
            venue='San Jose State University - The Event Center',
            venue_address='San Jose State University - The Event Center\n290 South 7th Street\nSan Jose, CA 95112\nUSA',
            normalized_location=Location(
                city=u'San Jose',
                country=u'United States',
                country_short=u'US',
                formatted_address=u'290 S 7th St, San Jose, CA 95112, USA',
                lat_lng=ndb.GeoPt(37.335228099999988, -121.88008170000001),
                name=u'The Event Center at SJSU',
                place_details={
                    u'website': u'http://www.union.sjsu.edu/',
                    u'rating': 3.7999999999999998,
                    u'utc_offset': -480,
                    u'name': u'The Event Center at SJSU',
                    u'reference': u'CmRRAAAAjFjECa6W4ywZsQrRghAULcxRk9agbN34AfqzQkAKCq2OACcTUjwjxiAoFH_LDlnvnJkxgwiolXaVhwaS5eHQ4qVk22EpEHW8KghrRpw0sAG1NeJ9JuaHOixtQAYmGmfmEhBQ94vPHaERHIbzc5SnUWOlGhTFUmg15SCaetWiglIEHFV3lwYs7g',
                    u'photos': [{
                        u'photo_reference': u'CoQBdwAAADDDIliDmADA3kHjRY00HBRWJwr_BpVFoKspAcWhq2gGxERwTPDF-9NnWLlPbuF8IAAg2ai_XskZHakIs3WClNGyvYuNjaRQvMPdlf-4CqIw26_AvKhHXuxYtTzLR0ZOPBzgAOS7Bd_tOUmiYvv9jV6XVzZjT3q89J-wl2qZP5JjEhAoiWhzxAxSLpPCDIckIu6YGhRtxFZS_WX7dFs_enaD3WygnmcHaA',
                        u'width': 4032,
                        u'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/105967386125327823641/photos">Markus Hoffmann</a>'],
                        u'height': 3024
                    }, {
                        u'photo_reference': u'CoQBdwAAAL2XQE18ncHM6L8uO9fbEV56Y-LDtn1AtBTjVMaOZEs6wCpkGZA0XbjKjHJgZxkNYqbN4gmau1mVu2AvNAF4Q8mrEmxUCTmvThIScg1_HJKxmg4I_DaVRVL1KcTgzBdfN16qaI--v67loRvcRp6QXedQL4D2QJdH6nQbYwBZGcdTEhDLMUxdXabIjQzbIxU05boOGhR7XEGVdS8AslciJOP80QXmXvk5YA',
                        u'width': 1944,
                        u'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/116297123282532291754/photos">William Marion</a>'],
                        u'height': 1944
                    }]
                },
                place_id=u'ChIJxclO9LjMj4ARnm8rZDR-fHs',
                postal_code=u'95112',
                state_prov=u'California',
                state_prov_short=u'CA',
                street=u'South 7th Street',
                street_number=u'290'
            ),
        ))
        self._test_to_and_back(events)

    def test_event_details_conversion(self):
        with open('test_data/usfirst_html/usfirst_event_rankings_2012ct.html', 'r') as f:
            rankings, _ = UsfirstEventRankingsParser.parse(f.read())
        event_details = EventDetails(
            id='2012ct',
            rankings=rankings,
            alliance_selections={
                '1': {'picks': ['frc254', 'frc469', 'frc2848', 'frc74'], 'declines': []},
                '2': {'picks': ['frc1718', 'frc2451', 'frc573', 'frc2016'], 'declines': []},
                '3': {'picks': ['frc2928', 'frc2013', 'frc1311', 'frc842'], 'declines': []},
                '4': {'picks': ['frc180', 'frc125', 'frc1323', 'frc2468'], 'declines': []},
                '5': {'picks': ['frc118', 'frc359', 'frc4334', 'frc865'], 'declines': []},
                '6': {'picks': ['frc135', 'frc1241', 'frc11', 'frc68'], 'declines': []},
                '7': {'picks': ['frc3478', 'frc177', 'frc294', 'frc230'], 'declines': []},
                '8': {'picks': ['frc624', 'frc987', 'frc3476', 'frc3015'], 'declines': []},
            },
            matchstats={'oprs': {'4255': 7.4877151786460301, '2643': 27.285682906835952, '852': 10.452538750544525, '4159': 25.820137009871139, '581': 18.513816255143144}}
        )
        self._test_to_and_back(event_details)

    def test_match_conversion(self):
        match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            score_breakdown_json=json.dumps({
                'red': {'auto': 20, 'assist': 40, 'truss+catch': 20, 'teleop_goal+foul': 20},
                'blue': {'auto': 40, 'assist': 60, 'truss+catch': 10, 'teleop_goal+foul': 40},
            }),
            comp_level="qm",
            event=ndb.Key('Event', '2012ct'),
            year=2012,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
            youtube_videos=[u'P3C2BOtL7e8', u'tst1', u'tst2', u'tst3'],
            time=datetime.datetime.now(),
            push_sent=True,
            tiebreak_match_key=ndb.Key('Match', '2012ct_qm2'),
        )
        self._test_to_and_back(match)

    def test_media_conversion(self):
        media = Media(id='cdphotothread_12058',
            created=datetime.datetime(2017, 6, 1, 2, 12, 33, 790650),
            details_json=u'{"image_partial": "c65/c65c9a3f2419e2cb0ccbc85cb73d14ea_l.jpg"}',
            foreign_key=u'12058',
            media_type_enum=1,
            preferred_references=[ndb.Key('Team', 'frc122')],
            private_details_json=None,
            references=[ndb.Key('Team', 'frc122')],
            updated=datetime.datetime(2017, 6, 1, 2, 12, 33, 790670),
            year=2001,
        )
        self._test_to_and_back(media)

    def test_robot_conversion(self):
        robot = Robot(
            id=Robot.renderKeyName('frc604', 2010),
            team=ndb.Key('Team', 'frc604'),
            year=2010,
            robot_name='OverKill',
            created=datetime.datetime.now() - datetime.timedelta(minutes=5),
            updated=datetime.datetime.now(),
        )
        self._test_to_and_back(robot)

    def test_team_conversion(self):
        team = Team(
            id='frc604',
            city=u'San Jose',
            country=u'USA',
            created=datetime.datetime(2012, 12, 10, 5, 43, 49, 283990),
            first_tpid=520751,
            first_tpid_year=2017,
            home_cmp=u'cmptx',
            motto=u'It will work - because it has to.',
            name=u"Leland High School FRC Team 604 Quixilver/IBM/Team Grandma/The Brin Wojcicki Foundation/BAE Systems/Qualcomm/Intuitive Surgical/Leland Bridge/Councilman J. Khamis/Almaden Valley Women's Club/NVIDIA/Exatron/MDR Precision/SOLIDWORKS/Dropbox/GitHub/Hurricane Electric&Leland High",
            nickname=u'Quixilver',
            normalized_location=Location(
                city=u'San Jose',
                country=u'United States',
                country_short=u'US',
                formatted_address=u'San Jose, CA 95120, USA',
                lat_lng=ndb.GeoPt(37.169699899999998, -121.8448745),
                name=None,
                place_details={
                    u'utc_offset': -480,
                    u'name': u'95120',
                    u'reference': u'CmRbAAAAhjUVxDNCrJ_jWkn6BTvFjToVI7e9HHbRbRr9Og0eZ-Mr_jzcwuTsw9zKk_tIAIAD_vNL1dr3yexSkadTNUluKsmWcZUz6RUR_EPz7A0oc2rPUTsmxAUAVpynAfabUpR_EhAWVARZXxDabJ5eWPw40dDFGhQuz5KpuNtGL23PbppeYZkPJ3dJQA',
                    u'geometry': {u'location': {u'lat': 37.169699899999998, u'lng': -121.8448745},
                    u'viewport': {u'northeast': {u'lat': 37.243775100000001, u'lng': -121.76169},
                    u'southwest': {u'lat': 37.107636100000001, u'lng': -121.91392089999999}}},
                    u'adr_address': u'<span class="locality">San Jose</span>, <span class="region">CA</span> <span class="postal-code">95120</span>, <span class="country-name">USA</span>',
                    u'place_id': u'ChIJ7dRTL0AwjoARro34O1rqo6g',
                    u'vicinity': u'San Jose',
                    u'url': u'https://maps.google.com/?q=95120&ftid=0x808e30402f53d4ed:0xa8a3ea5a3bf88dae',
                    u'scope': u'GOOGLE',
                    u'address_components': [{
                        u'long_name': u'95120',
                        u'types': [u'postal_code'],
                        u'short_name': u'95120'
                    }, {
                        u'long_name': u'San Jose',
                        u'types': [u'locality', u'political'],
                        u'short_name': u'San Jose'
                    }, {
                        u'long_name': u'Santa Clara County',
                        u'types': [u'administrative_area_level_2', u'political'],
                        u'short_name': u'Santa Clara County'
                    }, {
                        u'long_name': u'California',
                        u'types': [u'administrative_area_level_1', u'political'],
                        u'short_name': u'CA'
                    }, {
                        u'long_name': u'United States',
                        u'types': [u'country', u'political'],
                        u'short_name': u'US'
                    }],
                    u'formatted_address': u'San Jose, CA 95120, USA',
                    u'id': u'0637f37c618a6d8b86db543e6ad730db4824979e',
                },
                place_id=u'ChIJ7dRTL0AwjoARro34O1rqo6g',
                postal_code=u'95120',
                state_prov=u'California',
                state_prov_short=u'CA',
                street=None,
                street_number=None
            ),
            postalcode=u'95120',
            rookie_year=2001,
            school_name=u'Leland High',
            state_prov=u'California',
            team_number=604,
            updated=datetime.datetime(2017, 7, 31, 15, 24, 21, 215120),
            website=u'http://604Robotics.com',
        )
        self._test_to_and_back(team)
