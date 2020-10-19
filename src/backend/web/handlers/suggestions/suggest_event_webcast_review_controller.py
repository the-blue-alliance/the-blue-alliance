from flask import redirect, request
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.models.webcast import Webcast
from backend.web.handlers.suggestions.suggestion_review_base import (
    SuggestionsReviewBase,
)
from backend.web.profiled_render import render_template


class SuggestEventWebcastReviewController(SuggestionsReviewBase[Event]):
    REQUIRED_PERMISSIONS = [AccountPermission.REVIEW_MEDIA]

    def __init__(self, *args, **kw):
        super(SuggestEventWebcastReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion: Suggestion) -> Event:
        webcast = Webcast(
            type=request.form.get("webcast_type"),
            channel=request.form.get("webcast_channel"),
        )
        if request.form.get("webcast_file"):
            webcast["file"] = request.form.get("webcast_file")
        if request.form.get("webcast_date"):
            webcast["date"] = request.form.get("webcast_date")

        event = Event.get_by_id(request.form.get("event_key"))

        # This used to defer?
        EventWebcastAdder.add_webcast(event, webcast)
        return event

    """
    View the list of suggestions.
    """

    def get(self) -> Response:
        super().get()
        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "event")
        )

        suggestions_by_event_key = {}
        for suggestion in suggestions:
            if "webcast_dict" in suggestion.contents:
                suggestion.webcast_template = "webcast/{}.html".format(
                    suggestion.contents["webcast_dict"]["type"]
                )
            suggestions_by_event_key.setdefault(suggestion.target_key, []).append(
                suggestion
            )

        suggestion_sets = []
        for event_key, suggestions in suggestions_by_event_key.items():
            suggestion_sets.append(
                {"event": Event.get_by_id(event_key), "suggestions": suggestions}
            )

        template_values = {
            "event_key": request.args.get("event_key"),
            "success": request.args.get("success"),
            "suggestion_sets": suggestion_sets,
        }

        return render_template(
            "suggestions/suggest_event_webcast_review_list.html", template_values
        )

    def post(self) -> Response:
        super().post()
        event_key = request.form.get("event_key")
        verdict = request.form.get("verdict")
        if verdict == "accept":
            suggestion_key = request.form.get("suggestion_key")
            suggestion_key = (
                int(suggestion_key) if suggestion_key.isdigit() else suggestion_key
            )
            self._process_accepted(suggestion_key)
            return redirect(
                "/suggest/event/webcast/review?success=accept&event_key=%s" % event_key
            )

        elif verdict == "reject":
            suggestion_key = request.form.get("suggestion_key")
            suggestion_key = (
                int(suggestion_key) if suggestion_key.isdigit() else suggestion_key
            )
            self._process_rejected([suggestion_key])
            return redirect("/suggest/event/webcast/review?success=reject")

        elif verdict == "reject_all":
            suggestion_keys = request.form.get("suggestion_keys").split(",")
            suggestion_keys = [
                int(suggestion_key) if suggestion_key.isdigit() else suggestion_key
                for suggestion_key in suggestion_keys
            ]
            self._process_rejected(suggestion_keys)
            return redirect(
                f"/suggest/event/webcast/review?success=reject_all&event_key={event_key}"
            )

        return redirect("/suggest/event/webcast/review")
