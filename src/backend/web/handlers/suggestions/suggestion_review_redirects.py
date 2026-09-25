from typing import Callable, Dict, Optional

from flask import Blueprint, redirect
from werkzeug.wrappers import Response

from backend.common.consts.suggestion_type import SuggestionType
from backend.common.helpers.pwa_url_helper import PwaUrlHelper

"""
The moderator suggestion review UI moved to the PWA. These routes keep old
bookmarks and previously-posted Slack nags working by bouncing the retired
Jinja review URLs to their PWA equivalents.
"""

blueprint = Blueprint("suggestion_review_redirects", __name__)

# Retired Jinja review page -> the suggestion type the PWA reviews at
# /suggest/review/<type>
LEGACY_REVIEW_PATHS: Dict[str, Optional[SuggestionType]] = {
    "/suggest/review": None,
    "/suggest/apiwrite/review": SuggestionType.API_AUTH_ACCESS,
    "/suggest/cad/review": SuggestionType.ROBOT,
    "/suggest/event/media/review": SuggestionType.EVENT_MEDIA,
    "/suggest/event/webcast/review": SuggestionType.EVENT,
    "/suggest/offseason/review": SuggestionType.OFFSEASON_EVENT,
    "/suggest/match/video/review": SuggestionType.MATCH,
    "/suggest/team/media/review": SuggestionType.MEDIA,
    "/suggest/team/social/review": SuggestionType.SOCIAL_MEDIA,
}


def _make_redirect(
    suggestion_type: Optional[SuggestionType],
) -> Callable[[], Response]:
    def view() -> Response:
        return redirect(PwaUrlHelper.suggestion_review_url(suggestion_type))

    return view


for _path, _suggestion_type in LEGACY_REVIEW_PATHS.items():
    blueprint.add_url_rule(
        _path,
        endpoint=_path.strip("/").replace("/", "_"),
        view_func=_make_redirect(_suggestion_type),
        methods=["GET"],
    )
