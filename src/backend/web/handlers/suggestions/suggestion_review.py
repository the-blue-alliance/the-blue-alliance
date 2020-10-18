from flask import Blueprint, request
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import (
    AccountPermission,
    SUGGESTION_PERMISSIONS,
)
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.suggestion_fetcher import SuggestionFetcher
from backend.web.handlers.decorators import require_any_permission
from backend.web.profiled_render import render_template

blueprint = Blueprint("suggestion_review", __name__)


@blueprint.route("/suggest/review")
@require_any_permission(SUGGESTION_PERMISSIONS)
def suggest_review_home() -> Response:
    match_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "match"
    )
    event_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "event"
    )
    media_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "media"
    )
    event_media_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "event_media"
    )
    social_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "social-media"
    )
    offseason_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "offseason-event"
    )
    apiwrite_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "api_auth_access"
    )
    cad_count_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, "robot"
    )

    template_values = {
        "suggestions": {
            "match": match_count_future.get_result(),
            "event": event_count_future.get_result(),
            "media": media_count_future.get_result(),
            "event_media": event_media_count_future.get_result(),
            "social": social_count_future.get_result(),
            "offseason": offseason_count_future.get_result(),
            "apiwrite": apiwrite_count_future.get_result(),
            "cad": cad_count_future.get_result(),
        },
        "media_permission": AccountPermission.REVIEW_MEDIA,
        "offseason_permission": AccountPermission.REVIEW_OFFSEASON_EVENTS,
        "apiwrite_permission": AccountPermission.REVIEW_APIWRITE,
        "cad_permission": AccountPermission.REVIEW_DESIGNS,
        "event_media_permission": AccountPermission.REVIEW_EVENT_MEDIA,
        "status": request.args.get("status"),
    }

    return render_template("suggestions/suggest_review_home.html", template_values)
