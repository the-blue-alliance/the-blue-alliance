import unittest2

from google.appengine.ext import db
from google.appengine.ext import testbed

from controllers.datafeed_controller import UsfirstEventDetailsGet
from helpers.match_helper import MatchHelper
from datafeeds.offseason_matches_parser import OffseasonMatchesParser
from models.event import Event
from models.match import Match

def setupMatches(csv):
    with open(csv, 'r') as f:
        event = Event(
          id = "2013test",
          event_short = "test",
          year = 2013
        )
        
        parsed_matches = OffseasonMatchesParser.parse(f.read())
        matches = [Match(
            id = Match.renderKeyName(
                event, 
                match.get("comp_level", None), 
                match.get("set_number", 0), 
                match.get("match_number", 0)),
            event = event.key,
            game = Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number = match.get("set_number", 0),
            match_number = match.get("match_number", 0),
            comp_level = match.get("comp_level", None),
            team_key_names = match.get("team_key_names", None),
            alliances_json = match.get("alliances_json", None)
            )
            for match in parsed_matches]
        return matches

class TestMatchCleanup(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def test_cleanup(self):
        matches = setupMatches('test_data/cleanup_matches.csv')
        cleaned_matches = MatchHelper.deleteInvalidMatches(matches)
        indices = [9, 12, 26]
        for index in sorted(indices, reverse=True): #need to delete in reverse order so indices don't get messed up
            del matches[index]
        self.assertEqual(matches, cleaned_matches)
