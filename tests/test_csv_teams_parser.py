import unittest2

from datafeeds.csv_teams_parser import CSVTeamsParser


class TestCSVTeamsParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/teams.csv', 'r') as f:
            teams = CSVTeamsParser.parse(f.read())

        correct_teams = {
            1, 2, 3, 5, 9, 10, 15, 16, 18, 22, 100, 101, 102, 103, 999
        }
        self.assertEqual(teams.difference(correct_teams), set())
