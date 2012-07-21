import unittest2
import datetime

from google.appengine.ext import testbed
from google.appengine.api import urlfetch

from datafeeds.datafeed_usfirst_events import DatafeedUsfirstEvents

from models.team import Team

class TestDatafeedUsfirstEvents(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        
        self.datafeed = DatafeedUsfirstEvents()
    
    def tearDown(self):
        self.testbed.deactivate()
    
    def test_getEvent(self):
        # test with 2011ct
        event = self.datafeed.getEvent("5561", 2011)
        
        self.assertEqual(event.key().name(), "2011ct")
        self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event.event_type, "Regional")
        self.assertEqual(event.start_date, datetime.datetime(2011, 3, 31, 0, 0))
        self.assertEqual(event.end_date, datetime.datetime(2011, 4, 2, 0, 0))
        self.assertEqual(event.year, 2011)
        self.assertEqual(event.venue_address, "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event.website, "http://www.ctfirst.org/ctr")
        self.assertEqual(event.event_short, "ct")
    
    def test_getEventRegistration(self):
        # test with 2011ct
        teams = self.datafeed.getEventRegistration("5561", 2011)
        
        self.assertEqual(teams, [{'number': '383', 'tpid': '41829'}, {'number': '1124', 'tpid': '42285'}, {'number': '155', 'tpid': '41609'}, {'number': '3634', 'tpid': '51637'}, {'number': '999', 'tpid': '42215'}, {'number': '1699', 'tpid': '42751'}, {'number': '173', 'tpid': '41625'}, {'number': '175', 'tpid': '41629'}, {'number': '716', 'tpid': '42049'}, {'number': '178', 'tpid': '41635'}, {'number': '2170', 'tpid': '43331'}, {'number': '3146', 'tpid': '44577'}, {'number': '2168', 'tpid': '43335'}, {'number': '2067', 'tpid': '43175'}, {'number': '181', 'tpid': '41641'}, {'number': '1991', 'tpid': '43133'}, {'number': '3125', 'tpid': '44539'}, {'number': '2785', 'tpid': '44073'}, {'number': '1740', 'tpid': '42765'}, {'number': '1784', 'tpid': '42895'}, {'number': '3654', 'tpid': '51609'}, {'number': '3718', 'tpid': '49891'}, {'number': '558', 'tpid': '41939'}, {'number': '3719', 'tpid': '52081'}, {'number': '230', 'tpid': '41681'}, {'number': '3464', 'tpid': '49827'}, {'number': '177', 'tpid': '41633'}, {'number': '2064', 'tpid': '43159'}, {'number': '195', 'tpid': '41651'}, {'number': '3104', 'tpid': '44463'}, {'number': '3555', 'tpid': '49069'}, {'number': '3141', 'tpid': '44487'}, {'number': '3461', 'tpid': '47483'}, {'number': '3525', 'tpid': '48801'}, {'number': '237', 'tpid': '41691'}, {'number': '3182', 'tpid': '44547'}, {'number': '571', 'tpid': '41947'}, {'number': '176', 'tpid': '41631'}, {'number': '1071', 'tpid': '42251'}, {'number': '2836', 'tpid': '43965'}, {'number': '126', 'tpid': '41585'}, {'number': '157', 'tpid': '41611'}, {'number': '69', 'tpid': '41519'}, {'number': '1027', 'tpid': '42235'}, {'number': '663', 'tpid': '42007'}, {'number': '3585', 'tpid': '50743'}, {'number': '1073', 'tpid': '42255'}, {'number': '501', 'tpid': '41899'}, {'number': '869', 'tpid': '42131'}, {'number': '714', 'tpid': '42047'}, {'number': '1923', 'tpid': '42947'}, {'number': '743', 'tpid': '42051'}, {'number': '20', 'tpid': '41475'}, {'number': '3204', 'tpid': '44731'}, {'number': '1601', 'tpid': '42659'}, {'number': '2791', 'tpid': '43935'}, {'number': '533', 'tpid': '41919'}, {'number': '694', 'tpid': '42027'}])
      
    def test_getEventList(self):
        events = self.datafeed.getEventList(2011)
        
        self.assertEqual(len(events), 58) #58 events expected
        
        self.assertEqual(events[0]["first_eid"], "5519")
        self.assertEqual(events[0]["event_type"], "Regional")
        self.assertEqual(events[0]["name"], "BAE Systems/Granite State Regional ")
        
        self.assertEqual(events[1]["first_eid"], "5523")
        self.assertEqual(events[1]["event_type"], "Regional")
        self.assertEqual(events[1]["name"], "New Jersey Regional ")    