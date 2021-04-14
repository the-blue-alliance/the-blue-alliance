import unittest2
import json

from datafeeds.usfirst_matches_parser_2003 import UsfirstMatchesParser2003


@unittest2.skip
class TestUsfirstMatchesParser2003(unittest2.TestCase):
    def test_parse_2003sj(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2003sj.html', 'r') as f:
            matches, _ = UsfirstMatchesParser2003.parse(f.read())

        self.assertEqual(len(matches), 118)

        # Test 2003sj_qm1
        match = matches[14]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc973', u'frc359', u'frc632', u'frc480'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"red": {"teams": ["frc973", "frc359"], "score": 14}, "blue": {"teams": ["frc632", "frc480"], "score": 63}}"""))

        # Test 2003sj_qm5
        match = matches[18]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 5)
        self.assertEqual(match["team_key_names"], [u'frc159', u'frc376', u'frc1043', u'frc814'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"red": {"teams": ["frc159", "frc376"], "score": 31}, "blue": {"teams": ["frc1043", "frc814"], "score": 122}}"""))

        # Test 2003sj_qm104
        match = matches[-1]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 104)
        self.assertEqual(match["team_key_names"], [u'frc605', u'frc159', u'frc192', u'frc766'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"red": {"teams": ["frc605", "frc159"], "score": 42}, "blue": {"teams": ["frc192", "frc766"], "score": 70}}"""))

        # Test 2003sj_qf1m1
        match = matches[2]
        self.assertEqual(match["comp_level"], "qf")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc368', u'frc359', u'frc691', u'frc114'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"red": {"teams": ["frc368", "frc359"], "score": 33}, "blue": {"teams": ["frc691", "frc114"], "score": 7}}"""))

        # Test 2003sj_sf2m2
        match = matches[13]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc8', u'frc492', u'frc115', u'frc254'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"red": {"teams": ["frc8", "frc492"], "score": 26}, "blue": {"teams": ["frc115", "frc254"], "score": 53}}"""))

        # Test 2003sj_f1m2
        match = matches[1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc368', u'frc359', u'frc115', u'frc254'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"red": {"teams": ["frc368", "frc359"], "score": 50}, "blue": {"teams": ["frc115", "frc254"], "score": 6}}"""))

    def test_parse_2003cmp(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2003cmp.html', 'r') as f:
            matches, _ = UsfirstMatchesParser2003.parse(f.read())

        self.assertEqual(len(matches), 6)

        # Test 2003cmp_sf2m2
        match = matches[-1]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc343', u'frc25', u'frc292', u'frc302'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"teams": ["frc292", "frc302"], "score": 1}, "red": {"teams": ["frc343", "frc25"], "score": 43}}"""))

        # Test 2003cmp_f1m2
        match = matches[1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc111', u'frc65', u'frc343', u'frc25'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"teams": ["frc343", "frc25"], "score": 58}, "red": {"teams": ["frc111", "frc65"], "score": 10}}"""))
