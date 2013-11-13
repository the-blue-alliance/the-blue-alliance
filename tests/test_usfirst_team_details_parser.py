import unittest2

from datafeeds.usfirst_team_details_parser import UsfirstTeamDetailsParser


class TestUsfirstTeamDetailsParser(unittest2.TestCase):
    def test_parse_team_not_found(self):
        with open('test_data/usfirst_html/usfirst_team_details_team_not_found.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team, None)

    def test_parse_frc177_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc177_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"South Windsor, CT, USA")
        self.assertEqual(team["name"], "UTC Power/Ensign Bickford Aerospace & Defense & South Windsor High School")
        self.assertEqual(team["nickname"], "Bobcat Robotics")
        self.assertEqual(team["team_number"], 177)
        self.assertEqual(team["website"], "http://www.bobcatrobotics.org")

    def test_parse_frc1114_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc1114_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"St. Catharines, ON, Canada")
        self.assertEqual(team["name"], "Innovation First International/General Motors St. Catharines Powertrain & Simbotics")
        self.assertEqual(team["nickname"], "Simbotics")
        self.assertEqual(team["team_number"], 1114)
        self.assertEqual(team["website"], "http://www.simbotics.org")

    def test_parse_frc4590_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc4590_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"Kfar Hayarok, TA, Israel")
        self.assertEqual(team["name"], "Hakfar Hayarok")
        self.assertEqual(team["nickname"], "Greenblitz")
        self.assertEqual(team["team_number"], 4590)

    def test_parse_frc4756_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc4756_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["name"], "aaaaaa")
        self.assertEqual(team["nickname"], "wgogfom3")
        self.assertEqual(team["team_number"], 4756)

    def test_parse_frc1309_2004(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc1309_2004.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"Toronto, ON, Canada")
        self.assertEqual(team["name"], "Toronto District School Board & Emery Collegiate Institute")
        self.assertEqual(team["nickname"], "Diamond Eagles")
        self.assertEqual(team["team_number"], 1309)
