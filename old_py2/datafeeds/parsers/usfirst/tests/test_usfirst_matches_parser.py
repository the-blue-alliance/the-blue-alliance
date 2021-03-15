import unittest2

from datafeeds.usfirst_matches_parser import UsfirstMatchesParser


@unittest2.skip
class TestUsfirstMatchesParser(unittest2.TestCase):
    def test_parse_2012ct(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2012ct.html', 'r') as f:
            matches, _ = UsfirstMatchesParser.parse(f.read())

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

    def test_parse_2013cama(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2013cama.html', 'r') as f:
            matches, _ = UsfirstMatchesParser.parse(f.read())

        # Test 2013cama_qm1
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc3256', u'frc2135', u'frc1323', u'frc1678', u'frc4135', u'frc3501'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 58, "teams": ["frc1678", "frc4135", "frc3501"]}, "red": {"score": 5, "teams": ["frc3256", "frc2135", "frc1323"]}}""")
        self.assertEqual(match["time_string"], "9:00 AM")

        # Test 2013cama_f1m3
        match = matches[-1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 3)
        self.assertEqual(match["team_key_names"], [u'frc2643', u'frc3501', u'frc3970', u'frc295', u'frc840', u'frc1678'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 110, "teams": ["frc295", "frc840", "frc1678"]}, "red": {"score": 74, "teams": ["frc2643", "frc3501", "frc3970"]}}""")
        self.assertEqual(match["time_string"], "4:04 PM")

    def test_parse_2013casd(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2013casd.html', 'r') as f:
            matches, _ = UsfirstMatchesParser.parse(f.read())

        # Test 2013casd_qm1
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc3480', u'frc1159', u'frc2496', u'frc3453', u'frc702', u'frc4161'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 0, "teams": ["frc3453", "frc702", "frc4161"]}, "red": {"score": 32, "teams": ["frc3480", "frc1159", "frc2496"]}}""")
        self.assertEqual(match["time_string"], "9:00 AM")

    def test_parse_2013pahat_incomplete(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2013pahat_incomplete.html', 'r') as f:
            matches, _ = UsfirstMatchesParser.parse(f.read())

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

    def test_parse_2014test(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2014test.html', 'r') as f:
            matches, _ = UsfirstMatchesParser.parse(f.read())

        # Test 2014test_qm1, played match
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc7', u'frc9', u'frc12', u'frc3', u'frc2', u'frc11'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": 225, "teams": ["frc3", "frc2", "frc11"]}, "red": {"score": 45, "teams": ["frc7", "frc9", "frc12"]}}""")
        self.assertEqual(match["time_string"], "4:00 PM")

        # Test 2014test_qm16, unplayed match
        match = matches[15]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 16)
        self.assertEqual(match["team_key_names"], [u'frc9', u'frc2', u'frc1', u'frc13', u'frc3', u'frc10'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": -1, "teams": ["frc13", "frc3", "frc10"]}, "red": {"score": -1, "teams": ["frc9", "frc2", "frc1"]}}""")
        self.assertEqual(match["time_string"], "8:45 PM")
