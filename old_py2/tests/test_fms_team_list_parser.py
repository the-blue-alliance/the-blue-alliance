import unittest2

from datafeeds.fms_team_list_parser import FmsTeamListParser


class TestFmsTeamListParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/usfirst_html/fms_team_list_2012.html', 'r') as f:
            teams, _ = FmsTeamListParser.parse(f.read())

        # Test frc1
        team = teams[0]
        # self.assertEqual(team["address"], u'Pontiac, MI, USA')
        self.assertEqual(team["name"], u'BAE Systems/The Chrysler Fondation & Oakland Schools Technical Campus Northeast High School')
        self.assertEqual(team["nickname"], u'The Juggernauts')
        self.assertEqual(team["short_name"], u'ChryslerOSTCNE')
        self.assertEqual(team["team_number"], 1)

        # Test frc4403
        team = teams[-7]
        # self.assertEqual(team["address"], u'Torreon, CU, Mexico')
        self.assertEqual(team["name"], u'MET MEX PE\xd1OLES, S.A. DE C.V. & Tec de Monterrey Campus Laguna')
        self.assertEqual(team["nickname"], u'Pe\xf1oles-ITESM')
        self.assertEqual(team["short_name"], u'')
        self.assertEqual(team["team_number"], 4403)
