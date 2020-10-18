from typing import Optional

from flask import redirect, request
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.match_suggestion_accepter import MatchSuggestionAccepter
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.suggestion import Suggestion
from backend.web.handlers.decorators import require_permission
from backend.web.handlers.suggestions.suggestion_review_base import (
    SuggestionsReviewBase,
)
from backend.web.profiled_render import render_template


class SuggestMatchVideoReviewController(SuggestionsReviewBase[Match]):
    decorators = [require_permission(AccountPermission.REVIEW_MEDIA)]

    def __init__(self, *args, **kw):
        super(SuggestMatchVideoReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion: Suggestion) -> Optional[Match]:
        target_key = request.form.get(
            "key-{}".format(suggestion.key.id()), suggestion.target_key
        )
        match = Match.get_by_id(target_key)
        if not match:
            return None
        return MatchSuggestionAccepter.accept_suggestion(match, suggestion)

    """
    View the list of suggestions.
    """

    def get(self) -> Response:
        super().get()

        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "match")
            .fetch(limit=50)
        )

        # Roughly sort by event and match for easier review
        suggestions = sorted(suggestions, key=lambda s: s.target_key)

        event_futures = [
            Event.get_by_id_async(suggestion.target_key.split("_")[0])
            for suggestion in suggestions
        ]
        events = [event_future.get_result() for event_future in event_futures]

        template_values = {
            "suggestions_and_events": list(zip(suggestions, events)),
        }

        return render_template(
            "suggestions/suggest_match_video_review_list.html", template_values
        )

    def post(self) -> Response:
        super().post()

        accept_keys = []
        reject_keys = []
        for value in request.form.values():
            split_value = value.split("::")
            if len(split_value) == 2:
                key = split_value[1]
            else:
                continue
            if value.startswith("accept"):
                accept_keys.append(key)
            elif value.startswith("reject"):
                reject_keys.append(key)

        # Process accepts
        for accept_key in accept_keys:
            self._process_accepted(accept_key)

        # Process rejects
        self._process_rejected(reject_keys)

        return redirect("/suggest/match/video/review")
