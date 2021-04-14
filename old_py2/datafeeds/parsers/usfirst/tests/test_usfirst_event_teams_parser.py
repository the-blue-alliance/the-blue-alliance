import unittest2

from datafeeds.usfirst_event_teams_parser import UsfirstEventTeamsParser


@unittest2.skip
class TestUsfirstEventTeamsParser(unittest2.TestCase):
    def test_parse(self):
        teams = []
        with open('test_data/usfirst_html/usfirst_event_teams_2012ct-1.html', 'r') as f:
            partial_teams, more_pages1 = UsfirstEventTeamsParser.parse(f.read())
            teams.extend(partial_teams)
        with open('test_data/usfirst_html/usfirst_event_teams_2012ct-2.html', 'r') as f:
            partial_teams, more_pages2 = UsfirstEventTeamsParser.parse(f.read())
            teams.extend(partial_teams)
        with open('test_data/usfirst_html/usfirst_event_teams_2012ct-3.html', 'r') as f:
            partial_teams, more_pages3 = UsfirstEventTeamsParser.parse(f.read())
            teams.extend(partial_teams)

        sort_key = lambda t: t['team_number']
        self.assertEqual(sorted(teams, key=sort_key),
                         sorted([{'first_tpid': 62407, 'team_number': 1124}, {'first_tpid': 61747, 'team_number': 155}, {'first_tpid': 65461, 'team_number': 3634}, {'first_tpid': 62391, 'team_number': 1099}, {'first_tpid': 62339, 'team_number': 999}, {'first_tpid': 62827, 'team_number': 1699}, {'first_tpid': 61763, 'team_number': 173}, {'first_tpid': 61767, 'team_number': 175}, {'first_tpid': 61773, 'team_number': 178}, {'first_tpid': 63343, 'team_number': 2170}, {'first_tpid': 64443, 'team_number': 3146}, {'first_tpid': 63347, 'team_number': 2168}, {'first_tpid': 63209, 'team_number': 2067}, {'first_tpid': 61779, 'team_number': 181}, {'first_tpid': 63169, 'team_number': 1991}, {'first_tpid': 64005, 'team_number': 2785}, {'first_tpid': 62841, 'team_number': 1740}, {'first_tpid': 62963, 'team_number': 1784}, {'first_tpid': 61815, 'team_number': 228}, {'first_tpid': 65459, 'team_number': 3654}, {'first_tpid': 65159, 'team_number': 3718}, {'first_tpid': 62069, 'team_number': 558}, {'first_tpid': 65535, 'team_number': 3719}, {'first_tpid': 61827, 'team_number': 236}, {'first_tpid': 61819, 'team_number': 230}, {'first_tpid': 65145, 'team_number': 3464}, {'first_tpid': 61771, 'team_number': 177}, {'first_tpid': 61789, 'team_number': 195}, {'first_tpid': 64351, 'team_number': 3104}, {'first_tpid': 65045, 'team_number': 3555}, {'first_tpid': 64881, 'team_number': 3461}, {'first_tpid': 65017, 'team_number': 3525}, {'first_tpid': 61829, 'team_number': 237}, {'first_tpid': 64419, 'team_number': 3182}, {'first_tpid': 62077, 'team_number': 571}, {'first_tpid': 61769, 'team_number': 176}, {'first_tpid': 71713, 'team_number': 4055}, {'first_tpid': 62373, 'team_number': 1071}, {'first_tpid': 63913, 'team_number': 2836}, {'first_tpid': 62229, 'team_number': 839}, {'first_tpid': 61723, 'team_number': 126}, {'first_tpid': 64859, 'team_number': 549}, {'first_tpid': 62359, 'team_number': 1027}, {'first_tpid': 62137, 'team_number': 663}, {'first_tpid': 63077, 'team_number': 1922}, {'first_tpid': 62377, 'team_number': 1073}, {'first_tpid': 61685, 'team_number': 95}, {'first_tpid': 64947, 'team_number': 3467}, {'first_tpid': 62257, 'team_number': 869}, {'first_tpid': 62635, 'team_number': 1493}, {'first_tpid': 72789, 'team_number': 4134}, {'first_tpid': 62181, 'team_number': 743}, {'first_tpid': 61615, 'team_number': 20}, {'first_tpid': 61843, 'team_number': 250}, {'first_tpid': 63903, 'team_number': 3017}, {'first_tpid': 62799, 'team_number': 1665}, {'first_tpid': 63885, 'team_number': 2791}, {'first_tpid': 62157, 'team_number': 694}, {'first_tpid': 63063, 'team_number': 1880}, {'first_tpid': 68707, 'team_number': 4122}, {'first_tpid': 62653, 'team_number': 1511}, {'first_tpid': 61817, 'team_number': 229}, {'first_tpid': 62707, 'team_number': 1559}, {'first_tpid': 61711, 'team_number': 118}], key=sort_key))
        self.assertEqual(more_pages1, True)
        self.assertEqual(more_pages2, True)
        self.assertEqual(more_pages3, False)
