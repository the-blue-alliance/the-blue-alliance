import unittest2
import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.ext.webapp import Response

from controllers.datafeed_controller import UsfirstEventGet

from models import Event, Team

class TestUsfirstEventGet(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        
    def tearDown(self):
        self.testbed.deactivate()
    
    def test_get(self):
        # test with 2011ct
        usfirsteventget = UsfirstEventGet()
        usfirsteventget.response = Response()
        usfirsteventget.get("5561", 2011)
        
        # check event object got created
        event = Event.get_by_key_name("2011ct")
        self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event.event_type, "Regional")
        self.assertEqual(event.start_date, datetime.datetime(2011, 3, 31, 0, 0))
        self.assertEqual(event.end_date, datetime.datetime(2011, 4, 2, 0, 0))
        self.assertEqual(event.year, 2011)
        self.assertEqual(event.venue_address, "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event.website, "http://www.ctfirst.org/ctr")
        self.assertEqual(event.event_short, "ct")
        
        # check team objects get created for missing teams
        frc177 = Team.get_by_key_name("frc177")
        self.assertEqual(frc177.team_number, 177)
        self.assertEqual(frc177.first_tpid, 41633)

