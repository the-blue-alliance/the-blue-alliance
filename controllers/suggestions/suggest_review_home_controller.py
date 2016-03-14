import os

from google.appengine.ext.webapp import template

from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.suggestion_fetcher import SuggestionFetcher
from models.suggestion import Suggestion


class SuggestReviewHomeController(SuggestionsReviewBaseController):
    """The main view for a data reviewer to see the state of pending suggestions."""
    def get(self):
        self.template_values['suggestions'] = dict()
        self.template_values['suggestions']['match'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "match")
        self.template_values['suggestions']['event'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "event")
        self.template_values['suggestions']['media'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "media")

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_review_home.html')
        self.response.out.write(template.render(path, self.template_values))
