import unittest2
import json

from datafeeds.usfirst_matches_parser_2002 import UsfirstMatchesParser2002


@unittest2.skip
class TestUsfirstMatchesParser2002(unittest2.TestCase):
    def test_parse_2002sj(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2002sj.html', 'r') as f:
            matches, _ = UsfirstMatchesParser2002.parse(f.read())

        self.assertEqual(len(matches), 128)

        # Test 2002sj_qm1
        match = matches[0]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc814', u'frc604', u'frc295', u'frc254'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 28, "teams": ["frc295", "frc254"]}, "red": {"score": 10, "teams": ["frc814", "frc604"]}}"""))

        # Test 2002sj_qm5
        match = matches[4]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 5)
        self.assertEqual(match["team_key_names"], [u'frc609', u'frc852', u'frc359', u'frc258'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 27, "teams": ["frc359", "frc258"]}, "red": {"score": 40, "teams": ["frc609", "frc852"]}}"""))

        # Test 2002sj_qm111
        match = matches[110]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 111)
        self.assertEqual(match["team_key_names"], [u'frc841', u'frc100', u'frc254', u'frc524'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 40, "teams": ["frc254", "frc524"]}, "red": {"score": 37, "teams": ["frc841", "frc100"]}}"""))

        # Test 2002sj_qf1m1
        match = matches[111]
        self.assertEqual(match["comp_level"], "qf")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc254', u'frc60', u'frc359', u'frc298', u'frc368', u'frc409'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 10, "teams": ["frc298", "frc368", "frc409"]}, "red": {"score": 49, "teams": ["frc254", "frc60", "frc359"]}}"""))

        # Test 2002sj_sf2m2
        match = matches[-3]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc8', u'frc609', u'frc100', u'frc701', u'frc376', u'frc115'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 20, "teams": ["frc701", "frc376", "frc115"]}, "red": {"score": 13, "teams": ["frc8", "frc609", "frc100"]}}"""))

        # Test 2002sj_f1m2
        match = matches[-1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc254', u'frc60', u'frc359', u'frc701', u'frc376', u'frc115'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 20, "teams": ["frc701", "frc376", "frc115"]}, "red": {"score": 41, "teams": ["frc254", "frc60", "frc359"]}}"""))

    def test_parse_2002tx(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2002tx.html', 'r') as f:
            matches, _ = UsfirstMatchesParser2002.parse(f.read())

        self.assertEqual(len(matches), 111)

        # Test 2002tx_qm11
        match = matches[10]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 11)
        self.assertEqual(match["team_key_names"], [u'frc317', u'frc442', u'frc624', u'frc922'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 31, "teams": ["frc624", "frc922"]}, "red": {"score": 32, "teams": ["frc317", "frc442"]}}"""))

        # Test 2002tx_qm52
        match = matches[51]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 52)
        self.assertEqual(match["team_key_names"], [u'frc231', u'frc356', u'frc499', u'frc908'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 39, "teams": ["frc499", "frc908"]}, "red": {"score": 32, "teams": ["frc231", "frc356"]}}"""))

        # Test 2002sj_qf2m1
        match = matches[-12]
        self.assertEqual(match["comp_level"], "qf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 1)
        self.assertEqual(match["team_key_names"], [u'frc57', u'frc357', u'frc481', u'frc317', u'frc624', u'frc704'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 20, "teams": ["frc317", "frc624", "frc704"]}, "red": {"score": 35, "teams": ["frc57", "frc357", "frc481"]}}"""))

        # Test 2002sj_sf2m2
        match = matches[-3]
        self.assertEqual(match["comp_level"], "sf")
        self.assertEqual(match["set_number"], 2)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc635', u'frc476', u'frc437', u'frc34', u'frc457', u'frc192'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 35, "teams": ["frc34", "frc457", "frc192"]}, "red": {"score": 20, "teams": ["frc635", "frc476", "frc437"]}}"""))

        # Test 2002sj_f1m2
        match = matches[-1]
        self.assertEqual(match["comp_level"], "f")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc16', u'frc118', u'frc609', u'frc34', u'frc457', u'frc192'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"score": 25, "teams": ["frc34", "frc457", "frc192"]}, "red": {"score": 11, "teams": ["frc16", "frc118", "frc609"]}}"""))

    def test_parse_2002va(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2002va.html', 'r') as f:
            matches, _ = UsfirstMatchesParser2002.parse(f.read())

        self.assertEqual(len(matches), 132)

        # Test 2002va_qm2
        match = matches[1]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 2)
        self.assertEqual(match["team_key_names"], [u'frc602', u'frc900', u'frc975', u'frc769'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"teams": ["frc975", "frc769"], "score": 31}, "red": {"teams": ["frc602", "frc900"], "score": 21}}"""))

        # Test 2002va_qm16
        match = matches[15]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 16)
        self.assertEqual(match["team_key_names"], [u'frc837', u'frc587', u'frc825', u'frc345'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"teams": ["frc825", "frc345"], "score": 35}, "red": {"teams": ["frc837", "frc587"], "score": 35}}"""))

        # Test 2002va_qm132
        match = matches[-1]
        self.assertEqual(match["comp_level"], "qm")
        self.assertEqual(match["set_number"], 1)
        self.assertEqual(match["match_number"], 132)
        self.assertEqual(match["team_key_names"], [u'frc414', u'frc837', u'frc400', u'frc53'])
        self.assertEqual(json.loads(match["alliances_json"]), json.loads("""{"blue": {"teams": ["frc400", "frc53"], "score": 40}, "red": {"teams": ["frc414", "frc837"], "score": 11}}"""))
