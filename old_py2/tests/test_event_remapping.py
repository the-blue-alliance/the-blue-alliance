import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event_helper import EventHelper
from models.award import Award
from models.match import Match


class TestEventRemapping(unittest2.TestCase):
    remap_teams = {
        'frc9001': 'frc1B',
        'frc2': 'frc200',
    }

    def test_remapteams_matches(self):
        matches = [Match(
            id="2019casj_qm1",
            alliances_json="""{"blue": {"score": 100, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": 200, "teams": ["frc4", "frc5", "frc9001"]}}""",
        )]
        EventHelper.remapteams_matches(matches, self.remap_teams)
        self.assertEqual(matches[0].alliances['blue']['teams'], ['frc1', 'frc200', 'frc3'])
        self.assertEqual(set(matches[0].team_key_names), set(['frc4', 'frc5', 'frc1B', 'frc1', 'frc200', 'frc3']))

    def test_remap_alliances(self):
        alliances = [
            {"declines": [], "backup": None, "name": "Alliance 1", "picks": ["frc9001", "frc649", "frc840"]},
            {"declines": [], "backup": None, "name": "Alliance 2", "picks": ["frc254", "frc5499", "frc6418"]},
            {"declines": [], "backup": None, "name": "Alliance 3", "picks": ["frc1868", "frc8", "frc4990"]},
            {"declines": [], "backup": None, "name": "Alliance 4", "picks": ["frc604", "frc2", "frc7308"]},
            {"declines": [], "backup": None, "name": "Alliance 5", "picks": ["frc199", "frc5026", "frc192"]},
            {"declines": [], "backup": None, "name": "Alliance 6", "picks": ["frc4669", "frc2220", "frc766"]},
            {"declines": [], "backup": None, "name": "Alliance 7", "picks": ["frc7419", "frc7667", "frc751"]},
            {"declines": [], "backup": None, "name": "Alliance 8", "picks": ["frc2367", "frc2473", "frc6241"]},
        ]
        EventHelper.remapteams_alliances(alliances, self.remap_teams)
        self.assertEqual(alliances[0]['picks'], ['frc1B', 'frc649', 'frc840'])
        self.assertEqual(alliances[3]['picks'], ['frc604', 'frc200', 'frc7308'])

    def test_remap_awards(self):
        awards = [
            Award(
                recipient_json_list=["""{"team_number": 2, "awardee": null}"""]
            ),
        ]
        EventHelper.remapteams_awards(awards, self.remap_teams)
        self.assertEqual(awards[0].recipient_list[0]['team_number'], '200')
        self.assertEqual(awards[0].team_list, [ndb.Key('Team', 'frc200')])
