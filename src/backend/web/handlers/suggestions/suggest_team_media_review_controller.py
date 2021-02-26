import json
from typing import Optional

from flask import redirect, request
from google.cloud import ndb
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import IMAGE_TYPES
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.media_creator import MediaCreator
from backend.web.handlers.suggestions.suggestion_review_base import (
    SuggestionsReviewBase,
)
from backend.web.profiled_render import render_template


class SuggestTeamMediaReviewController(SuggestionsReviewBase[Media]):
    REQUIRED_PERMISSIONS = [AccountPermission.REVIEW_MEDIA]
    ALLOW_TEAM_ADMIN_ACCESS = True

    def __init__(self, *args, **kw):
        self.preferred_keys = []
        super(SuggestTeamMediaReviewController, self).__init__(*args, **kw)

    """
    View the list of suggestions.
    """

    def get(self) -> Response:
        super().get()

        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "media")
            .fetch(limit=50)
        )

        # Quick and dirty way to group images together
        suggestions = sorted(
            suggestions,
            key=lambda x: 0 if x.contents["media_type_enum"] in IMAGE_TYPES else 1,
        )

        reference_keys = []
        existing_preferred_keys_futures = []
        for suggestion in suggestions:
            reference_key = suggestion.contents["reference_key"]
            reference = Media.create_reference(
                suggestion.contents["reference_type"], reference_key
            )
            reference_keys.append(reference)

            if "details_json" in suggestion.contents:
                suggestion.details = json.loads(suggestion.contents["details_json"])
                if "image_partial" in suggestion.details:
                    suggestion.details["thumbnail"] = suggestion.details[
                        "image_partial"
                    ].replace("_l", "_m")

            # Find existing preferred images
            existing_preferred_keys_futures.append(
                Media.query(
                    Media.media_type_enum.IN(IMAGE_TYPES),  # pyre-ignore[16]
                    Media.references == reference,
                    Media.preferred_references == reference,
                    Media.year == suggestion.contents["year"],
                ).fetch_async(keys_only=True)
            )

        reference_futures = ndb.get_multi_async(reference_keys)
        existing_preferred_futures = map(
            lambda x: ndb.get_multi_async(x.get_result()),
            existing_preferred_keys_futures,
        )

        references = map(lambda r: r.get_result(), reference_futures)
        existing_preferred = map(
            lambda l: list(map(lambda x: x.get_result(), l)), existing_preferred_futures
        )

        suggestions_and_references_and_preferred = zip(
            suggestions, list(references), list(existing_preferred)
        )

        template_values = {
            "suggestions_and_references_and_preferred": list(
                suggestions_and_references_and_preferred
            ),
            "max_preferred": Media.MAX_PREFERRED,
        }

        return render_template(
            "suggestions/suggest_team_media_review_list.html", template_values
        )

    def create_target_model(self, suggestion: Suggestion) -> Optional[Media]:
        # Setup
        to_replace: Optional[Media] = None
        to_replace_id = request.form.get(
            "replace-preferred-{}".format(suggestion.key.id()), None
        )
        year = int(
            request.form.get(f"year-{suggestion.key.id()}", suggestion.contents["year"])
        )

        # Override year if necessary
        suggestion.contents["year"] = year
        suggestion.contents_json = json.dumps(suggestion.contents)
        suggestion._contents = None

        # Remove preferred reference from another Media if specified
        team_reference = Media.create_reference(
            suggestion.contents["reference_type"], suggestion.contents["reference_key"]
        )
        if to_replace_id:
            to_replace = Media.get_by_id(to_replace_id)
            if team_reference not in to_replace.preferred_references:
                # Preferred reference must have been edited earlier. Skip this Suggestion for now.
                return None
            to_replace.preferred_references.remove(team_reference)

        # Add preferred reference to current Media (images only) if explicitly listed in preferred_keys or if to_replace_id exists
        media_type_enum = suggestion.contents["media_type_enum"]
        preferred_references = []
        if media_type_enum in IMAGE_TYPES and (
            "preferred::{}".format(suggestion.key.id()) in self.preferred_keys
            or to_replace_id
        ):
            preferred_references = [team_reference]

        media = MediaCreator.create_media_model(
            suggestion, team_reference, preferred_references
        )

        # Do all DB writes
        if to_replace:
            MediaManipulator.createOrUpdate(to_replace, auto_union=False)
        return MediaManipulator.createOrUpdate(media)

    def post(self) -> Response:
        super().post()

        self.preferred_keys = request.form.getlist("preferred_keys[]")
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

        return_url = request.args.get("return_url", "/suggest/team/media/review")
        return redirect(return_url)
