import unittest2
import webtest
import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.district_type import DistrictType
from consts.event_type import EventType

from controllers.api.api_district_controller import ApiDistrictListController, ApiDistrictEventsController, ApiDistrictRankingsController

from models.event import Event
from models.event_details import EventDetails
from models.team import Team
from models.match import Match
from models.event_team import EventTeam


class TestListDistrictsController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<year:>', ApiDistrictListController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.event = Event(
                id="2010sc",
                name="Palmetto Regional",
                event_type_enum=EventType.DISTRICT_CMP,
                event_district_enum=DistrictType.NEW_ENGLAND,
                short_name="Palmetto",
                event_short="sc",
                year=2010,
                end_date=datetime(2010, 03, 27),
                official=True,
                city="Clemson",
                state_prov="SC",
                country="USA",
                venue="Long Beach Arena",
                venue_address="Long Beach Arena\r\n300 East Ocean Blvd\r\nLong Beach, CA 90802\r\nUSA",
                start_date=datetime(2010, 03, 24),
                webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
                website="http://www.firstsv.org",
        )
        self.event.put()

        self.event_details = EventDetails(
            id=self.event.key.id(),
            alliance_selections=[
                {"declines": [], "picks": ["frc971", "frc254", "frc1662"]},
                {"declines": [], "picks": ["frc1678", "frc368", "frc4171"]},
                {"declines": [], "picks": ["frc2035", "frc192", "frc4990"]},
                {"declines": [], "picks": ["frc1323", "frc846", "frc2135"]},
                {"declines": [], "picks": ["frc2144", "frc1388", "frc668"]},
                {"declines": [], "picks": ["frc1280", "frc604", "frc100"]},
                {"declines": [], "picks": ["frc114", "frc852", "frc841"]},
                {"declines": [], "picks": ["frc2473", "frc3256", "frc1868"]}
            ]
        )
        self.event_details.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertDistrictKeys(self, district):
        self.assertEqual(district["key"], DistrictType.type_abbrevs[DistrictType.NEW_ENGLAND])
        self.assertEqual(district["name"], DistrictType.type_names[DistrictType.NEW_ENGLAND])

    def testDistrictApi(self):
        response = self.testapp.get('/{}'.format(self.event.year), headers={"X-TBA-App-Id": "tba-tests:disstrict-controller-test:v01"})

        districts = json.loads(response.body)
        self.assertDistrictKeys(districts[0])


class TestListDistrictEventsController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<district_abbrev:>/<year:>', ApiDistrictEventsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.event = Event(
                id="2010sc",
                name="Palmetto Regional",
                event_type_enum=EventType.DISTRICT_CMP,
                event_district_enum=DistrictType.NEW_ENGLAND,
                short_name="Palmetto",
                event_short="sc",
                year=2010,
                end_date=datetime(2010, 03, 27),
                official=True,
                city="Clemson",
                state_prov="SC",
                country="USA",
                venue="Long Beach Arena",
                venue_address="Long Beach Arena\r\n300 East Ocean Blvd\r\nLong Beach, CA 90802\r\nUSA",
                start_date=datetime(2010, 03, 24),
                webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
                website="http://www.firstsv.org",
        )
        self.event.put()

        self.event_details = EventDetails(
            id=self.event.key.id(),
            alliance_selections=[
                {"declines": [], "picks": ["frc971", "frc254", "frc1662"]},
                {"declines": [], "picks": ["frc1678", "frc368", "frc4171"]},
                {"declines": [], "picks": ["frc2035", "frc192", "frc4990"]},
                {"declines": [], "picks": ["frc1323", "frc846", "frc2135"]},
                {"declines": [], "picks": ["frc2144", "frc1388", "frc668"]},
                {"declines": [], "picks": ["frc1280", "frc604", "frc100"]},
                {"declines": [], "picks": ["frc114", "frc852", "frc841"]},
                {"declines": [], "picks": ["frc2473", "frc3256", "frc1868"]}
            ]
        )
        self.event_details.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertDistrictEvent(self, event):
        self.assertEqual(event["key"], self.event.key_name)
        self.assertEqual(event["name"], self.event.name)
        self.assertEqual(event["short_name"], self.event.short_name)
        self.assertEqual(event["official"], self.event.official)
        self.assertEqual(event["event_type_string"], self.event.event_type_str)
        self.assertEqual(event["event_type"], self.event.event_type_enum)
        self.assertEqual(event["event_district_string"], self.event.event_district_str)
        self.assertEqual(event["event_district"], self.event.event_district_enum)
        self.assertEqual(event["start_date"], self.event.start_date.date().isoformat())
        self.assertEqual(event["end_date"], self.event.end_date.date().isoformat())
        self.assertEqual(event["location"], self.event.location)
        self.assertEqual(event["venue_address"], self.event.venue_address.replace('\r\n', '\n'))
        self.assertEqual(event["webcast"], json.loads(self.event.webcast_json))
        self.assertEqual(event["alliances"], self.event.alliance_selections)
        self.assertEqual(event["website"], self.event.website)

    def testEventApi(self):
        response = self.testapp.get("/{}/2010".format(DistrictType.type_abbrevs[self.event.event_district_enum]), headers={"X-TBA-App-Id": "tba-tests:disstrict-controller-test:v01"})

        events = json.loads(response.body)
        self.assertDistrictEvent(events[0])


class TestListDistrictEventsController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/<district_abbrev:>/<year:>', ApiDistrictEventsController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.event = Event(
                id="2010sc",
                name="Palmetto Regional",
                event_type_enum=EventType.DISTRICT_CMP,
                event_district_enum=DistrictType.NEW_ENGLAND,
                short_name="Palmetto",
                event_short="sc",
                year=2010,
                end_date=datetime(2010, 03, 27),
                official=True,
                city="Clemson",
                state_prov="SC",
                country="USA",
                venue="Long Beach Arena",
                venue_address="Long Beach Arena\r\n300 East Ocean Blvd\r\nLong Beach, CA 90802\r\nUSA",
                start_date=datetime(2010, 03, 24),
                webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
                website="http://www.firstsv.org",
        )
        self.event.put()

        self.event_details = EventDetails(
            id=self.event.key.id(),
            alliance_selections=[
                {"declines": [], "picks": ["frc971", "frc254", "frc1662"]},
                {"declines": [], "picks": ["frc1678", "frc368", "frc4171"]},
                {"declines": [], "picks": ["frc2035", "frc192", "frc4990"]},
                {"declines": [], "picks": ["frc1323", "frc846", "frc2135"]},
                {"declines": [], "picks": ["frc2144", "frc1388", "frc668"]},
                {"declines": [], "picks": ["frc1280", "frc604", "frc100"]},
                {"declines": [], "picks": ["frc114", "frc852", "frc841"]},
                {"declines": [], "picks": ["frc2473", "frc3256", "frc1868"]}
            ]
        )
        self.event_details.put()

    def tearDown(self):
        self.testbed.deactivate()

    def assertDistrictEvent(self, event):
        self.assertEqual(event["key"], self.event.key_name)
        self.assertEqual(event["name"], self.event.name)
        self.assertEqual(event["short_name"], self.event.short_name)
        self.assertEqual(event["official"], self.event.official)
        self.assertEqual(event["event_type_string"], self.event.event_type_str)
        self.assertEqual(event["event_type"], self.event.event_type_enum)
        self.assertEqual(event["event_district_string"], self.event.event_district_str)
        self.assertEqual(event["event_district"], self.event.event_district_enum)
        self.assertEqual(event["start_date"], self.event.start_date.date().isoformat())
        self.assertEqual(event["end_date"], self.event.end_date.date().isoformat())
        self.assertEqual(event["location"], self.event.location)
        self.assertEqual(event["venue_address"], self.event.venue_address.replace('\r\n', '\n'))
        self.assertEqual(event["webcast"], json.loads(self.event.webcast_json))
        self.assertEqual(event["alliances"], self.event.alliance_selections)
        self.assertEqual(event["website"], self.event.website)

    def testEventApi(self):
        response = self.testapp.get("/{}/2010".format(DistrictType.type_abbrevs[self.event.event_district_enum]), headers={"X-TBA-App-Id": "tba-tests:disstrict-controller-test:v01"})

        events = json.loads(response.body)
        self.assertDistrictEvent(events[0])

