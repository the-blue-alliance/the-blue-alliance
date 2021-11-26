from google.appengine.ext import ndb

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.suggestion_fetcher import SuggestionFetcher
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion


def test_count(ndb_context):
    Suggestion(
        author=ndb.Key(Account, "foo@bar.com"),
        review_state=SuggestionState.REVIEW_PENDING,
        target_key="2012cmp",
        target_model="event",
    ).put()

    assert (
        SuggestionFetcher.count_async(
            SuggestionState.REVIEW_PENDING, "event"
        ).get_result()
        == 1
    )
    assert (
        SuggestionFetcher.count_async(
            SuggestionState.REVIEW_PENDING, "media"
        ).get_result()
        == 0
    )
