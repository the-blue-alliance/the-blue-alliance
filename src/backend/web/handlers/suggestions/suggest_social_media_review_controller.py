from typing import Optional

from flask import redirect, request
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.media_creator import MediaCreator
from backend.web.handlers.suggestions.suggestion_review_base import (
    SuggestionsReviewBase,
)
from backend.web.profiled_render import render_template


class SuggestSocialMediaReviewController(SuggestionsReviewBase[Media]):
    REQUIRED_PERMISSIONS = [AccountPermission.REVIEW_MEDIA]
    ALLOW_TEAM_ADMIN_ACCESS = True

    def __init__(self, *args, **kw) -> None:
        super(SuggestSocialMediaReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion: Suggestion) -> Optional[Media]:
        # Create a basic Media from this suggestion
        return MediaCreator.from_suggestion(suggestion)

    """
    View the list of suggestions.
    """

    def get(self) -> Response:
        super().get()
        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "social-media")
            .fetch(limit=50)
        )

        reference_keys = []
        for suggestion in suggestions:
            reference_key = suggestion.contents["reference_key"]
            reference = Media.create_reference(
                suggestion.contents["reference_type"], reference_key
            )
            reference_keys.append(reference)

        reference_futures = ndb.get_multi_async(reference_keys)
        references = map(lambda r: r.get_result(), reference_futures)
        suggestions_and_references = list(zip(suggestions, references))

        template_values = {
            "suggestions_and_references": suggestions_and_references,
        }

        return render_template(
            "suggestions/suggest_team_social_review.html", template_values
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

        return_url = request.form.get("return_url", "/suggest/team/social/review")
        return redirect(return_url)
