import unittest2

from datafeeds.usfirst_matches_parser import UsfirstMatchesParser

class TestUsfirstMatchesParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2012ct.html', 'r') as f:
            matches = UsfirstMatchesParser.parse(f.read())

        # Test 2012ct_qm1
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc1073', u'frc549', u'frc1991', u'frc999', u'frc3464', u'frc126'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 31, "teams": ["frc999", "frc3464", "frc126"]}, "red": {"score": 37, "teams": ["frc1073", "frc549", "frc1991"]}}""")
        
        # Test 2012ct_sf2m1
        match = matches[-7]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc177', u'frc228', u'frc236', u'frc20', u'frc181', u'frc195'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 76, "teams": ["frc20", "frc181", "frc195"]}, "red": {"score": 41, "teams": ["frc177", "frc228", "frc236"]}}""")
        
        # Test 2012ct_f1m3
        match = matches[-1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 3)
        self.assertEqual(match["team_key_names"], [u'frc1071', u'frc558', u'frc2067', u'frc195', u'frc181', u'frc20'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 62, "teams": ["frc195", "frc181", "frc20"]}, "red": {"score": 39, "teams": ["frc1071", "frc558", "frc2067"]}}""")
