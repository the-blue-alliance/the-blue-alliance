import unittest2
import datetime

from google.appengine.ext import testbed

from datafeeds.datafeed_usfirst_teams2 import DatafeedUsfirstTeams2

class TestDatafeedUsfirstTeams2(unittest2.TestCase):
    
    TEST_HTML_FILE = "test_data/usfirst_html/usfirst_fms_teamlist.html"
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        
        self.datafeed = DatafeedUsfirstTeams2()
    
    def tearDown(self):
        self.testbed.deactivate()
    
    def test_getAllCurrentSeasonTeams(self):
        teams = self.datafeed.getAllCurrentSeasonTeams()
        self.find177(teams)
    
    def test__parseHtml(self):
        test_file = open(self.TEST_HTML_FILE,"r")
        teams = self.datafeed._parseHtml(test_file.read())
        self.find177(teams)
    
    def find177(self, teams):
        found_177 = False
        for team in teams:
            if team["team_number"] == "177":
                found_177 = True
                self.assertEqual(team["name"], "UTC Power/Ensign Bickford Aerospace & Defense & South Windsor High School")
                self.assertEqual(team["address"], u"South Windsor, CT, USA")
                self.assertEqual(team["nickname"], "Bobcat Robotics")
        
        self.assertTrue(found_177)
        self.assertTrue(len(teams) > 0)

