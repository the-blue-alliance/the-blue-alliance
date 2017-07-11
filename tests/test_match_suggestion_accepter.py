import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from helpers.suggestions.match_suggestion_accepter import MatchSuggestionAccepter
from models.account import Account
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion


class TestMatchSuggestionAccepter(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.account = Account(
            email="tba@thebluealliance.com",
        )
        self.account.put()

        self.suggestion = Suggestion(
            author=self.account.key,
            contents_json="{\"youtube_videos\":[\"123456\"]}",
            target_key="2012ct_qm1",
            target_model="match"
        )
        self.suggestion.put()

        self.event = Event(
            id="2012ct",
            event_short="ct",
            year=2012,
            event_type_enum=EventType.REGIONAL
        )
        self.event.put()

        self.match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            comp_level="qm",
            event=self.event.key,
            year=2012,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
            youtube_videos=["abcdef"]
        )
        self.match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_accept_suggestions(self):
        MatchSuggestionAccepter.accept_suggestion(self.match, self.suggestion)

        match = Match.get_by_id("2012ct_qm1")
        self.assertTrue("abcdef" in match.youtube_videos)
        self.assertTrue("123456" in match.youtube_videos)
