import unittest2
import datetime

from google.appengine.ext import db
from google.appengine.ext import testbed

from datafeeds.datafeed_usfirst_matches import DatafeedUsfirstMatches
from models.event import Event

class TestDatafeedUsfirstMatches(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        
        self.datafeed = DatafeedUsfirstMatches()
    
    def tearDown(self):
        self.testbed.deactivate()
    
    def test_getMatchResultsList(self):
        event = Event(
          key_name = "2011ct",
          event_short = "ct",
          year = 2011
        )
        
        matches = self.datafeed.getMatchResultsList(event)
        
        # Test 2011ct_qm1
        match = matches[0]
        self.assertEqual(match.key().name(), "2011ct_qm1")
        self.assertEqual(match.game, "frc_2011_logo")
        self.assertEqual(match.comp_level, "qm")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 1)
        self.assertEqual(match.team_key_names, [u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'])
        self.assertEqual(match.alliances_json, """{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""")
        
        # Test 2011ct_qf2m3
        match = matches[-7]
        self.assertEqual(match.key().name(), "2011ct_qf2m3")
        self.assertEqual(match.game, "frc_2011_logo")
        self.assertEqual(match.comp_level, "qf")
        self.assertEqual(match.set_number, 2)
        self.assertEqual(match.match_number, 3)
        self.assertEqual(match.team_key_names, [u'frc716', u'frc3125', u'frc181', u'frc1699', u'frc1124', u'frc714'])
        self.assertEqual(match.alliances_json, """{"blue": {"score": 74, "teams": ["frc1699", "frc1124", "frc714"]}, "red": {"score": 90, "teams": ["frc716", "frc3125", "frc181"]}}""")
        
        # Test 2011ct_f1m2
        match = matches[-1]
        self.assertEqual(match.key().name(), "2011ct_f1m2")
        self.assertEqual(match.game, "frc_2011_logo")
        self.assertEqual(match.comp_level, "f")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 2)
        self.assertEqual(match.team_key_names, [u'frc195', u'frc1923', u'frc155', u'frc177', u'frc175', u'frc1073'])
        self.assertEqual(match.alliances_json, """{"blue": {"score": 65, "teams": ["frc177", "frc175", "frc1073"]}, "red": {"score": 97, "teams": ["frc195", "frc1923", "frc155"]}}""")