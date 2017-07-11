import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from datafeeds.usfirst_matches_parser import UsfirstMatchesParser
from helpers.match_helper import MatchHelper
from models.event import Event
from models.match import Match


class TestAddMatchTimes(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.event = Event(
            id="2014casj",
            event_short="casj",
            event_type_enum=EventType.REGIONAL,
            name="Silicon Valley Regional",
            start_date=datetime.datetime(2014, 2, 27, 0, 0),
            end_date=datetime.datetime(2014, 3, 1, 0, 0),
            year=2014,
            timezone_id="America/New_York",
        )

        self.event_dst = Event(
            id="2014casj",
            event_short="casj",
            event_type_enum=EventType.REGIONAL,
            name="Silicon Valley Regional",
            start_date=datetime.datetime(2014, 3, 8, 0, 0),
            end_date=datetime.datetime(2014, 3, 9, 0, 0),  # chosen to span DST change
            year=2014,
            timezone_id="America/Los_Angeles",
        )

    def matchDictToMatches(self, match_dicts):
        return [Match(id=Match.renderKeyName(self.event.key.id(),
                                             match_dict.get("comp_level", None),
                                             match_dict.get("set_number", 0),
                                             match_dict.get("match_number", 0)),
                      event=self.event.key,
                      year=self.event.year,
                      set_number=match_dict.get("set_number", 0),
                      match_number=match_dict.get("match_number", 0),
                      comp_level=match_dict.get("comp_level", None),
                      team_key_names=match_dict.get("team_key_names", None),
                      time_string=match_dict.get("time_string", None),
                      alliances_json=match_dict.get("alliances_json", None))
                for match_dict in match_dicts]

    def test_match_times(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2013cama.html', 'r') as f:  # using matches from a random event as data
            match_dicts, _ = UsfirstMatchesParser.parse(f.read())

        matches = self.matchDictToMatches(match_dicts)
        MatchHelper.add_match_times(self.event, matches)

        self.assertEqual(len(matches), 92)

        PST_OFFSET = -5
        self.assertEqual(matches[0].time, datetime.datetime(2014, 2, 28, 9, 0) - datetime.timedelta(hours=PST_OFFSET))
        self.assertEqual(matches[75].time, datetime.datetime(2014, 3, 1, 11, 50) - datetime.timedelta(hours=PST_OFFSET))

    def test_match_times_dst(self):
        with open('test_data/usfirst_html/usfirst_event_matches_2012ct.html', 'r') as f:  # using matches from a random event as data
            match_dicts, _ = UsfirstMatchesParser.parse(f.read())

        matches = self.matchDictToMatches(match_dicts)
        MatchHelper.add_match_times(self.event_dst, matches)

        self.assertEqual(len(matches), 125)

        PST_OFFSET = -8
        PDT_OFFSET = -7
        self.assertEqual(matches[0].time, datetime.datetime(2014, 3, 8, 9, 0) - datetime.timedelta(hours=PST_OFFSET))
        self.assertEqual(matches[-1].time, datetime.datetime(2014, 3, 9, 16, 5) - datetime.timedelta(hours=PDT_OFFSET))
