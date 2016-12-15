import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.match_suggestion_accepter import MatchSuggestionAccepter
from models.match import Match
from models.suggestion import Suggestion


class SuggestMatchVideoReviewController(SuggestionsReviewBaseController):

    def __init__(self, *args, **kw):
        self.REQUIRED_PERMISSIONS.append(AccountPermissions.REVIEW_MEDIA)
        super(SuggestMatchVideoReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        match = Match.get_by_id(suggestion.target_key)
        return MatchSuggestionAccepter.accept_suggestion(match, suggestion)

    """
    View the list of suggestions.
    """
    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "match").fetch(limit=50)

        # Roughly sort by event and match for easier review
        suggestions = sorted(suggestions, key=lambda s: s.target_key)

        self.template_values.update({
            "suggestions": suggestions,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_match_video_review_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        accept_keys = map(lambda x: int(x) if x.isdigit() else x, self.request.POST.getall("accept_keys[]"))
        reject_keys = map(lambda x: int(x) if x.isdigit() else x, self.request.POST.getall("reject_keys[]"))

        for accept_key in accept_keys:
            self._process_accepted(accept_key)

        self._process_rejected(reject_keys)

        self.redirect("/suggest/match/video/review")
