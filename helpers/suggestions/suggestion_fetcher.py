from google.appengine.ext import ndb

from models.suggestion import Suggestion

class SuggestionFetcher(object):
    @classmethod
    def count(self, review_state, suggestion_type):
        """Return the count of suggestions of a particular type with a particular state."""
        return Suggestion.query().filter(
            Suggestion.review_state == review_state).filter(
            Suggestion.target_model == suggestion_type).count()
