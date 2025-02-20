from datetime import timedelta

from flask import (
    Blueprint,
    jsonify,
    make_response,
    redirect,
    request,
    Response,
    url_for,
)
from pyre_extensions import none_throws
from werkzeug.wrappers import Response as WerkzeugResponse

from backend.common.auth import current_user
from backend.common.consts.notification_type import (
    ENABLED_NOTIFICATIONS,
    NotificationType,
)
from backend.common.consts.notification_type import TYPES as NOTIFICATION_TYPES
from backend.common.decorators import cached_public
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.web.decorators import enforce_login
from backend.web.profiled_render import render_template


blueprint = Blueprint("apidocs", __name__, url_prefix="/apidocs")


@blueprint.route("")
@cached_public(ttl=timedelta(weeks=1))
def apidocs_overview() -> str:
    return render_template("apidocs_overview.html")


@blueprint.route("/trusted")
def apidocs_trusted() -> WerkzeugResponse:
    return redirect(url_for("apidocs.apidocs_trusted_v1"))


@blueprint.route("/trusted/v1")
@cached_public(ttl=timedelta(weeks=1))
def apidocs_trusted_v1() -> str:
    template_values = {
        "title": "Trusted APIv1",
        "swagger_url": "/swagger/api_trusted_v1.json",
    }
    return render_template("apidocs_swagger.html", template_values)


@blueprint.route("/v3")
@cached_public(ttl=timedelta(weeks=1))
def apidocs_v3() -> str:
    template_values = {
        "title": "APIv3",
        "swagger_url": "/swagger/api_v3.json",
    }
    return render_template("apidocs_swagger.html", template_values)


@blueprint.route("/webhooks")
# @cached_public(ttl=timedelta(weeks=1))
# TODO: Figure out how we can cache this despite having a CSRF token in the form
def apidocs_webhooks() -> str:
    template_values = {"enabled": ENABLED_NOTIFICATIONS, "types": NOTIFICATION_TYPES}
    return render_template("apidocs_webhooks.html", template_values)


@blueprint.route("/webhooks/test/<int:type>", methods=["POST"])
@enforce_login
def apidocs_webhooks_notification(type: int) -> Response:
    event_key = request.form.get("event_key")
    match_key = request.form.get("match_key")
    # district_key = request.form.get("district_key")

    user = none_throws(current_user())
    user_id = str(user.uid)

    success_response = make_response("ok", 200)

    def error_response(message: str):
        return make_response(jsonify({"Error": message}), 400)

    try:
        notification_type = NotificationType(type)
    except ValueError:
        return error_response("Invalid notification type")

    if notification_type in [
        NotificationType.ALLIANCE_SELECTION,
        NotificationType.AWARDS,
        NotificationType.SCHEDULE_UPDATED,
    ]:
        # Handle our Event dispatches
        if not event_key:
            return error_response("Event key not specified")

        from backend.common.models.event import Event

        event = Event.get_by_id(event_key)
        if not event:
            return error_response(f"Event {event_key} not found")

        if notification_type == NotificationType.ALLIANCE_SELECTION:
            TBANSHelper.alliance_selection(event, user_id=user_id)
            return success_response
        elif notification_type == NotificationType.AWARDS:
            TBANSHelper.awards(event, user_id=user_id)
            return success_response
        elif notification_type == NotificationType.SCHEDULE_UPDATED:
            TBANSHelper.event_schedule(event, user_id=user_id)
            return success_response

        return error_response("Unexpected error")
    elif notification_type in [
        NotificationType.UPCOMING_MATCH,
        NotificationType.MATCH_SCORE,
        NotificationType.LEVEL_STARTING,
        NotificationType.MATCH_VIDEO,
    ]:
        # Handle our Match dispatches
        if not match_key:
            return error_response("Match key not specified")

        from backend.common.models.match import Match

        match = Match.get_by_id(match_key)
        if not match:
            return error_response(f"Match {match_key} not found")

        if notification_type == NotificationType.UPCOMING_MATCH:
            TBANSHelper.match_upcoming(match, user_id=user_id)
            return success_response
        elif notification_type == NotificationType.MATCH_SCORE:
            TBANSHelper.match_score(match, user_id=user_id)
            return success_response
        elif notification_type == NotificationType.LEVEL_STARTING:
            TBANSHelper.event_level(match, user_id=user_id)
            return success_response
        elif notification_type == NotificationType.MATCH_VIDEO:
            TBANSHelper.match_video(match, user_id=user_id)
            return success_response

        return error_response("Unexpected error")

    # TODO: Need to handle district_points_updated here as well

    return error_response(f"Unknown notification_type {notification_type}")
