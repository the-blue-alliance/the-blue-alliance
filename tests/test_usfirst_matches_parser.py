import unittest2

from datafeeds.usfirst_matches_parser import UsfirstMatchesParser

class TestUsfirstMatchesParser(unittest2.TestCase):
    def test_parse_2012ct(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2012ct.html', 'r') as f:
            matches = UsfirstMatchesParser.parse(f.read())

        # Test 2012ct_qm1
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc1073', u'frc549', u'frc1991', u'frc999', u'frc3464', u'frc126'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 31, "teams": ["frc999", "frc3464", "frc126"]}, "red": {"score": 37, "teams": ["frc1073", "frc549", "frc1991"]}}""")
        self.assertEqual(match["time_string"], "9:00 AM")

        # Test 2012ct_sf2m1
        match = matches[-7]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc177', u'frc228', u'frc236', u'frc20', u'frc181', u'frc195'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 76, "teams": ["frc20", "frc181", "frc195"]}, "red": {"score": 41, "teams": ["frc177", "frc228", "frc236"]}}""")
        self.assertEqual(match["time_string"], "2:51 PM")

        # Test 2012ct_f1m3
        match = matches[-1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 3)
        self.assertEqual(match["team_key_names"], [u'frc1071', u'frc558', u'frc2067', u'frc195', u'frc181', u'frc20'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 62, "teams": ["frc195", "frc181", "frc20"]}, "red": {"score": 39, "teams": ["frc1071", "frc558", "frc2067"]}}""")
        self.assertEqual(match["time_string"], "4:05 PM")

    def test_parse_2013pahat_incomplete(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2013pahat_incomplete.html', 'r') as f:
            matches = UsfirstMatchesParser.parse(f.read())

        # Test 2013pahat_qm1, played match
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc4342', u'frc3151', u'frc1647', u'frc816', u'frc3974', u'frc3123'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 66, "teams": ["frc816", "frc3974", "frc3123"]}, "red": {"score": 35, "teams": ["frc4342", "frc3151", "frc1647"]}}""")
        self.assertEqual(match["time_string"], "11:30 AM")

        # Test 2013pahat_qm37, unplayed match
        match = matches[36]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 37)
        self.assertEqual(match["team_key_names"], [u'frc1143', u'frc2729', u'frc3123', u'frc87', u'frc304', u'frc1495'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": -1, "teams": ["frc87", "frc304", "frc1495"]}, "red": {"score": -1, "teams": ["frc1143", "frc2729", "frc3123"]}}""")
        self.assertEqual(match["time_string"], "5:32 PM")
