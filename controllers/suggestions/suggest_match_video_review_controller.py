from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.match_suggestion_accepter import MatchSuggestionAccepter
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestMatchVideoReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_MEDIA]

    def __init__(self, *args, **kw):
        super(SuggestMatchVideoReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        target_key = self.request.get('key-{}'.format(suggestion.key.id()), suggestion.target_key)
        match = Match.get_by_id(target_key)
        if not match:
            return None
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

        event_futures = [Event.get_by_id_async(suggestion.target_key.split("_")[0]) for suggestion in suggestions]
        events = [event_future.get_result() for event_future in event_futures]

        self.template_values.update({
            "suggestions_and_events": zip(suggestions, events),
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_match_video_review_list.html', self.template_values))

    def post(self):
        accept_keys = []
        reject_keys = []
        for value in self.request.POST.values():
            split_value = value.split('::')
            if len(split_value) == 2:
                key = split_value[1]
            else:
                continue
            if value.startswith('accept'):
                accept_keys.append(key)
            elif value.startswith('reject'):
                reject_keys.append(key)

        # Process accepts
        for accept_key in accept_keys:
            self._process_accepted(accept_key)

        # Process rejects
        self._process_rejected(reject_keys)

        self.redirect("/suggest/match/video/review")
