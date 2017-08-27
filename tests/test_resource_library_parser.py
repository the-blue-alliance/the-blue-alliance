import unittest2
import json

from datafeeds.resource_library_parser import ResourceLibraryParser


class TestResourceLibraryParser(unittest2.TestCase):
    def test_parse_hall_of_fame(self):
        with open('test_data/hall_of_fame.html', 'r') as f:
            teams, _ = ResourceLibraryParser.parse(f.read())

        # Test number of teams
        self.assertEqual(len(teams), 14)

        # Test team 987
        team = teams[0]
        self.assertEqual(team["team_id"], "frc987")
        self.assertEqual(team["team_number"], 987)
        self.assertEqual(team["year"], 2016)
        self.assertEqual(team["video"], "wpv-9yd_CJk")
        self.assertEqual(team["presentation"], "ILxVggTpXhs")
        self.assertEqual(team["essay"], "https://www.firstinspires.org/sites/default/files/uploads/resource_library/frc/game-and-season-info/awards/2016/chairmans/week-five/team-987.pdf")

        # Test team 597
        team = teams[1]
        self.assertEqual(team["team_id"], "frc597")
        self.assertEqual(team["team_number"], 597)
        self.assertEqual(team["year"], 2015)
        self.assertEqual(team["video"], "2FKks-d6LOo")
        self.assertEqual(team["presentation"], "RBXj490clow")
        self.assertEqual(team["essay"], None)

        # Test team 27
        team = teams[2]
        self.assertEqual(team["team_id"], "frc27")
        self.assertEqual(team["team_number"], 27)
        self.assertEqual(team["year"], 2014)
        self.assertEqual(team["video"], "BCz2yTVPxbM")
        self.assertEqual(team["presentation"], "1rE67fTRl98")
        self.assertEqual(team["essay"], "https://www.firstinspires.org/sites/default/files/uploads/resource_library/frc/game-and-season-info/awards/2015/2014-67-chairmans-handout.pdf")

        # Test team 1538
        team = teams[3]
        self.assertEqual(team["team_id"], "frc1538")
        self.assertEqual(team["team_number"], 1538)
        self.assertEqual(team["year"], 2013)
        self.assertEqual(team["video"], "p62jRCMkoiw")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 1114
        team = teams[4]
        self.assertEqual(team["team_id"], "frc1114")
        self.assertEqual(team["team_number"], 1114)
        self.assertEqual(team["year"], 2012)
        self.assertEqual(team["video"], "VqciMgjw-SY")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 359
        team = teams[5]
        self.assertEqual(team["team_id"], "frc359")
        self.assertEqual(team["team_number"], 359)
        self.assertEqual(team["year"], 2011)
        self.assertEqual(team["video"], "e9IV1chHJtg")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 341
        team = teams[6]
        self.assertEqual(team["team_id"], "frc341")
        self.assertEqual(team["team_number"], 341)
        self.assertEqual(team["year"], 2010)
        self.assertEqual(team["video"], "-AzvT02ZCNk")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 236
        team = teams[7]
        self.assertEqual(team["team_id"], "frc236")
        self.assertEqual(team["team_number"], 236)
        self.assertEqual(team["year"], 2009)
        self.assertEqual(team["video"], "NmzCLohIZLg")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 842
        team = teams[8]
        self.assertEqual(team["team_id"], "frc842")
        self.assertEqual(team["team_number"], 842)
        self.assertEqual(team["year"], 2008)
        self.assertEqual(team["video"], "N0LMLz6LK7U")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 365
        team = teams[9]
        self.assertEqual(team["team_id"], "frc365")
        self.assertEqual(team["team_number"], 365)
        self.assertEqual(team["year"], 2007)
        self.assertEqual(team["video"], "f8MT7pSRXtg")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)

        # Test team 111
        team = teams[10]
        self.assertEqual(team["team_id"], "frc111")
        self.assertEqual(team["team_number"], 111)
        self.assertEqual(team["year"], 2006)
        self.assertEqual(team["video"], "SfCjZMMIt0k")
        self.assertEqual(team["presentation"], None)
        self.assertEqual(team["essay"], None)
