from flask import Blueprint, request
from flask.helpers import make_response
from werkzeug.wrappers import Response

from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.match_suggestion_helper import MatchSuggestionHelper

blueprint = Blueprint("match_suggestions", __name__)


@blueprint.route("/tasks/do/update_match_suggestions")
def update_match_suggestions() -> Response:
    # The feed is deliberately not persisted: this cron recomputes it every
    # minute from live Datastore data and Firebase is the only consumer, so
    # there is nothing to `put`.
    suggestions = MatchSuggestionHelper.compute_match_suggestions()
    FirebasePusher.update_match_suggestions(suggestions)

    if "X-Appengine-Taskname" not in request.headers:
        return make_response(f"Pushed {len(suggestions.suggestions)} match suggestions")
    return make_response("")
