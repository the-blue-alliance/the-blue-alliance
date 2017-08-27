import datetime
import json
import unittest2

from consts.event_type import EventType
from datafeeds.parsers.fms_api.fms_api_awards_parser import FMSAPIAwardsParser
from datafeeds.parsers.fms_api.fms_api_event_list_parser import FMSAPIEventListParser
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from helpers.model_serializer import ModelSerializer
from models.award import Award
from models.event import Event
from models.location import Location
from models.robot import Robot


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
