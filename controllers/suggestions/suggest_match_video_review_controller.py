import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.match_suggestion_accepter import MatchSuggestionAccepter
from models.suggestion import Suggestion


class SuggestMatchVideoReviewController(SuggestionsReviewBaseController):
    """
    View the list of suggestions.
    """
    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "match").fetch(limit=50)

        self.template_values.update({
            "suggestions": suggestions,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_match_video_review_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        accept_keys = map(lambda x: int(x) if x.isdigit() else x, self.request.POST.getall("accept_keys[]"))
        reject_keys = map(lambda x: int(x) if x.isdigit() else x, self.request.POST.getall("reject_keys[]"))

        accepted_suggestion_futures = [Suggestion.get_by_id_async(key) for key in accept_keys]
        rejected_suggestion_futures = [Suggestion.get_by_id_async(key) for key in reject_keys]
        accepted_suggestions = map(lambda a: a.get_result(), accepted_suggestion_futures)
        rejected_suggestions = map(lambda a: a.get_result(), rejected_suggestion_futures)

        MatchSuggestionAccepter.accept_suggestions(accepted_suggestions)

        all_suggestions = accepted_suggestions
        all_suggestions.extend(rejected_suggestions)

        for suggestion in all_suggestions:
            if suggestion.key.id() in accept_keys:
                suggestion.review_state = Suggestion.REVIEW_ACCEPTED
            if suggestion.key.id() in reject_keys:
                suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.datetime.now()

        ndb.put_multi(all_suggestions)

        self.redirect("/suggest/match/video/review")
