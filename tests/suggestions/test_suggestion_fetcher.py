import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.account import Account
from models.suggestion import Suggestion

from helpers.suggestions.suggestion_fetcher import SuggestionFetcher


class TestSuggestionFetcher(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True).put()

        Suggestion(
            author=account,
            review_state=Suggestion.REVIEW_PENDING,
            target_key="2012cmp",
            target_model="event").put()

    def test_count(self):
        self.assertEqual(SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "event"), 1)
        self.assertEqual(SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "media"), 0)
