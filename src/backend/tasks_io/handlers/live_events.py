from flask import Blueprint

from backend.common.helpers.firebase_pusher import FirebasePusher

blueprint = Blueprint("live_events", __name__)


@blueprint.route("/tasks/do/update_live_events")
def update_live_events() -> str:
    FirebasePusher.update_live_events()
    return ""
