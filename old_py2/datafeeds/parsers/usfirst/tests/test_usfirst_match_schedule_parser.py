import unittest2

from datafeeds.usfirst_match_schedule_parser import UsfirstMatchScheduleParser


@unittest2.skip
class TestUsfirstMatchScheduleParser(unittest2.TestCase):
    def test_parse_2013casj_qual(self):
        with open('test_data/usfirst_html/usfirst_event_match_schedule_2013casj_qual.html', 'r') as f:
            matches, _ = UsfirstMatchScheduleParser.parse(f.read())

        self.assertEqual(len(matches), 99)

        # Test 2013casj_qm1
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc254', u'frc295', u'frc2489', u'frc1388', u'frc3482', u'frc649'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": -1, "teams": ["frc1388", "frc3482", "frc649"]}, "red": {"score": -1, "teams": ["frc254", "frc295", "frc2489"]}}""")
        self.assertEqual(match["time_string"], "9:00 AM")

    def test_parse_2013casj_elim(self):
        with open('test_data/usfirst_html/usfirst_event_match_schedule_2013casj_elim.html', 'r') as f:
            matches, _ = UsfirstMatchScheduleParser.parse(f.read())

        self.assertEqual(len(matches), 12)

        # Test 2013casj_qf4-3
        match = matches[-1]
        self.assertEqual(match["comp_level"], "qf")
        self.assertEqual(match["set_number"], 4)
        self.assertEqual(match["match_number"], 3)
        self.assertEqual(match["team_key_names"], [u'frc192', u'frc604', u'frc971', u'frc649', u'frc114', u'frc1388'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": -1, "teams": ["frc649", "frc114", "frc1388"]}, "red": {"score": -1, "teams": ["frc192", "frc604", "frc971"]}}""")
        self.assertEqual(match["time_string"], "2:58 PM")

    def test_parse_2014cmp_elim(self):
        with open('test_data/usfirst_html/usfirst_event_match_schedule_2014cmp_elim.html', 'r') as f:
            matches, _ = UsfirstMatchScheduleParser.parse(f.read())

        self.assertEqual(len(matches), 7)

        # Test 2014cmp_sf2-2
        match = matches[3]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc16', u'frc5', u'frc9', u'frc2', u'frc40', u'frc1'])
        self.assertEqual(match["alliances_json"], """{"blue": {"score": -1, "teams": ["frc2", "frc40", "frc1"]}, "red": {"score": -1, "teams": ["frc16", "frc5", "frc9"]}}""")
        self.assertEqual(match["time_string"], "5:29 PM")
