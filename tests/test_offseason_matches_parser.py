import unittest2

from datafeeds.offseason_matches_parser import OffseasonMatchesParser


class TestOffseasonMatchesParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/offseason_matches.csv', 'r') as f:
            matches, _ = OffseasonMatchesParser.parse(f.read())

        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], ['frc1', 'frc2', 'frc3', 'frc4', 'frc5', 'frc6'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 8, "teams": ["frc4", "frc5", "frc6"]}, "red": {"score": 7, "teams": ["frc1", "frc2", "frc3"]}}""")

        match = matches[1]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 22)
        self.assertEqual(match["team_key_names"], ['frc1', 'frc2', 'frc3', 'frc4', 'frc5', 'frc6'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": -1, "teams": ["frc4", "frc5", "frc6"]}, "red": {"score": -1, "teams": ["frc1", "frc2", "frc3"]}}""")

        match = matches[2]
        self.assertEqual(match["comp_level"], "qf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], ['frc1', 'frc2', 'frc3', 'frc4', 'frc5', 'frc6'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 8, "teams": ["frc4", "frc5", "frc6"]}, "red": {"score": 7, "teams": ["frc1", "frc2", "frc3"]}}""")

        match = matches[3]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 3)
        self.assertEqual(match["team_key_names"], ['frc1', 'frc2', 'frc3', 'frc4', 'frc5', 'frc6'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 8, "teams": ["frc4", "frc5", "frc6"]}, "red": {"score": 7, "teams": ["frc1", "frc2", "frc3"]}}""")

        match = matches[4]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], ['frc1', 'frc2', 'frc3', 'frc4', 'frc5', 'frc6'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 8, "teams": ["frc4", "frc5", "frc6"]}, "red": {"score": 7, "teams": ["frc1", "frc2", "frc3"]}}""")

        match = matches[5]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 99)
        self.assertEqual(match["team_key_names"], ['frc3', 'frc4', 'frc5'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 8, "teams": ["frc4", "frc5", "frc6A"]}, "red": {"score": 7, "teams": ["frc1A", "frc2B", "frc3"]}}""")

        match = matches[6]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 12)
        self.assertEqual(match["team_key_names"], ['frc3', 'frc1', 'frc2', 'frc6'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 8, "teams": ["frc1", "frc2", "frc6"]}, "red": {"score": 7, "teams": ["frc1B", "frc2B", "frc3"]}}""")
