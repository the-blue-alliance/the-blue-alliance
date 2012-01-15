import unittest2
import datetime

from google.appengine.ext import db
from google.appengine.ext import testbed

from datafeeds.datafeed_usfirst_teams import DatafeedUsfirstTeams
from models import Team

class TestDatafeedUsfirstTeams(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        
        self.datafeed = DatafeedUsfirstTeams()
        
        Team(
            key_name = "frc177",
            team_number = 177,
            first_tpid = 61771,
            first_tpid_year = 2012
        ).put()
        
    
    def test_getTeamDetails(self):
        team = self.datafeed.getTeamDetails(177)
        
        self.assertEqual(team.name, "UTC Power/Ensign Bickford Aerospace & Defense & South Windsor High School")
        self.assertEqual(team.address, u"South Windsor, CT\xa0 USA")
        self.assertEqual(team.nickname, "Bobcat Robotics")
        self.assertEqual(team.website, "http://www.bobcatrobotics.org")