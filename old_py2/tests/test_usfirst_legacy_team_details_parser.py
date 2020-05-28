import unittest2

from datafeeds.usfirst_legacy_team_details_parser import UsfirstLegacyTeamDetailsParser


@unittest2.skip
class TestUsfirstLegacyTeamDetailsParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/usfirst_legacy_html/usfirst_team_details_frc177_2012.html', 'r') as f:
            team, _ = UsfirstLegacyTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"South Windsor, CT\xa0 USA")
        self.assertEqual(team["name"], "UTC Power/Ensign Bickford Aerospace & Defense & South Windsor High School")
        self.assertEqual(team["nickname"], "Bobcat Robotics")
        self.assertEqual(team["team_number"], 177)
        self.assertEqual(team["rookie_year"], 1995)
        self.assertEqual(team["website"], "http://www.bobcatrobotics.org")
