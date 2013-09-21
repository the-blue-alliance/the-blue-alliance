import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.suggestions.match_suggestion_accepter import MatchSuggestionAccepter
from models.suggestion import Suggestion


class AdminEventWebcastSuggestionsReviewController(LoggedInHandler):
    """
    View the list of suggestions.
    """
    def get(self):
        self._require_admin()

        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "event")

        self.template_values.update({
            "suggestions": suggestions,
        })

        path = os.path.join(os.path.dirname(__file__), '../../../templates/admin/event_webcast_suggestion_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        # get the suggestion

        # maybe give it to an accepter

        # mark it accepted or rejected

        self.redirect("/admin/suggestions/event/webcast/review")