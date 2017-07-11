import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.match_helper import MatchHelper
from datafeeds.offseason_matches_parser import OffseasonMatchesParser
from models.event import Event
from models.match import Match


class TestMatchCleanup(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.event = Event(
            id="2013test",
            event_short="test",
            year=2013,
            event_type_enum=0,
        )
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def setupMatches(self, csv):
        with open(csv, 'r') as f:
            parsed_matches, _ = OffseasonMatchesParser.parse(f.read())
            matches = [Match(id=Match.renderKeyName(self.event.key.id(),
                                                    match.get("comp_level", None),
                                                    match.get("set_number", 0),
                                                    match.get("match_number", 0)),
                             event=self.event.key,
                             year=self.event.year,
                             set_number=match.get("set_number", 0),
                             match_number=match.get("match_number", 0),
                             comp_level=match.get("comp_level", None),
                             team_key_names=match.get("team_key_names", None),
                             alliances_json=match.get("alliances_json", None))
                       for match in parsed_matches]
            return matches

    def test_cleanup(self):
        matches = self.setupMatches('test_data/cleanup_matches.csv')
        cleaned_matches = MatchHelper.deleteInvalidMatches(matches, self.event)
        indices = {9, 12, 26}
        correct_matches = []
        for i, match in enumerate(matches):
            if i not in indices:
                correct_matches.append(match)
        self.assertEqual(correct_matches, cleaned_matches)
