from typing import Optional

from flask import redirect, request
from google.appengine.ext import ndb
from pyre_extensions import none_throws
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


class SuggestDesignsReviewController(SuggestionsReviewBase[Media]):
    REQUIRED_PERMISSIONS = [AccountPermission.REVIEW_DESIGNS]
    ALLOW_TEAM_ADMIN_ACCESS = True

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def create_target_model(self, suggestion: Suggestion) -> Optional[Media]:
        # Create a basic Media from this suggestion
        return MediaCreator.from_suggestion(suggestion)

    """
    View the list of suggestions.
    """

    def get(self) -> Response:
        super().get()
        if request.args.get("action") and request.args.get("id"):
            # Fast-path review
            return self._fastpath_review()

        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "robot")
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
            "suggestions/suggest_designs_review.html", template_values
        )

    def _fastpath_review(self) -> Response:
        suggestion: Optional[Suggestion] = Suggestion.get_by_id(
            request.args.get("id", "")
        )
        status = None
        if suggestion and suggestion.target_model == "robot":
            if suggestion.review_state == SuggestionState.REVIEW_PENDING:
                # slack_message = None
                if request.args.get("action") == "accept":
                    self._process_accepted(none_throws(suggestion.key.id()))
                    status = "accepted"
                    """
                    slack_message = u"{0} ({1}) accepted the <https://grabcad.com/library/{2}|suggestion> for team <https://www.thebluealliance.com/team/{3}/{4}|{3} in {4}>".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        suggestion.contents['foreign_key'],
                        suggestion.contents['reference_key'][3:],
                        suggestion.contents['year']
                    ).encode('utf-8')
                    """
                elif request.args.get("action") == "reject":
                    self._process_rejected([none_throws(suggestion.key.id())])
                    status = "rejected"
                    """
                    slack_message = u"{0} ({1}) rejected the <https://grabcad.com/library/{2}|suggestion> for team <https://www.thebluealliance.com/team/{3}/{4}|{3} in {4}>".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        suggestion.contents['foreign_key'],
                        suggestion.contents['reference_key'][3:],
                        suggestion.contents['year']
                    ).encode('utf-8')
                    """

                """
                TODO port outgoing stuff
                if slack_message:
                    slack_sitevar = Sitevar.get_or_insert('slack.hookurls')
                    if slack_sitevar:
                        slack_url = slack_sitevar.contents.get('tbablog', '')
                        OutgoingNotificationHelper.send_slack_alert(slack_url, slack_message)
                """
            else:
                status = "already_reviewed"
        else:
            status = "bad_suggestion"

        return redirect(f"/suggest/review?status={status}")

    def post(self) -> Response:
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

        return_url = request.form.get("return_url", "/suggest/cad/review")
        return redirect(return_url)
