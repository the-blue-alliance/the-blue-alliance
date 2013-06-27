import unittest2

from datafeeds.usfirst_team_details_parser import UsfirstTeamDetailsParser

class TestUsfirstTeamDetailsParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc177_2012-2.html', 'r') as f: 
            team = UsfirstTeamDetailsParser.parse(f.read())
        
        self.assertEqual(team["address"], u"South Windsor, CT\xa0 USA")
        self.assertEqual(team["name"], "UTC Power/Ensign Bickford Aerospace & Defense & South Windsor High School")
        self.assertEqual(team["nickname"], "Bobcat Robotics")
        self.assertEqual(team["team_number"], 177)
        self.assertEqual(team["website"], "http://www.bobcatrobotics.org")
