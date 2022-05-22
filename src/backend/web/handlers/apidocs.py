from datetime import timedelta

import requests
from flask import Blueprint, make_response, redirect, request, Response, url_for
from pyre_extensions import none_throws
from werkzeug.wrappers import Response as WerkzeugResponse

from backend.common.auth import current_user
from backend.common.consts.notification_type import (
    ENABLED_NOTIFICATIONS,
    NotificationType,
)
from backend.common.consts.notification_type import TYPES as NOTIFICATION_TYPES
from backend.common.decorators import cached_public
from backend.web.decorators import enforce_login
from backend.web.profiled_render import render_template


blueprint = Blueprint("apidocs", __name__, url_prefix="/apidocs")


@blueprint.route("/")
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
@cached_public(ttl=timedelta(weeks=1))
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
    user_id = user.uid
    data = {"user_id": user_id}

    success_response = make_response("ok", 200)
    error_response = make_response("", 400)
    origin = request.headers.get("Origin")

    import logging

    logging.warning(origin)

    try:
        notification_type = NotificationType(type)
    except ValueError:
        return error_response

    if notification_type in [
        NotificationType.ALLIANCE_SELECTION,
        NotificationType.AWARDS,
        NotificationType.SCHEDULE_UPDATED,
    ]:
        # Handle our Event dispatches
        if not event_key:
            return error_response

        # TODO: Update these... do NOT ned to be sync, right?
        if notification_type == NotificationType.ALLIANCE_SELECTION:
            requests.post(f"/tbans/alliance_selections/{event_key}", data=data)
            return success_response
        elif notification_type == NotificationType.AWARDS:
            requests.post(f"/tbans/awards/{event_key}", data=data)
            return success_response
        elif notification_type == NotificationType.SCHEDULE_UPDATED:
            requests.post(f"/tbans/event_schedule/{event_key}", data=data)
            return success_response

        return error_response
    elif notification_type in [
        NotificationType.UPCOMING_MATCH,
        NotificationType.MATCH_SCORE,
        NotificationType.LEVEL_STARTING,
        NotificationType.MATCH_VIDEO,
    ]:
        # Handle our Match dispatches
        if not match_key:
            return error_response

        if notification_type == NotificationType.UPCOMING_MATCH:
            requests.post(f"/tbans/match_upcoming/{match_key}", data=data)
            return success_response
        elif notification_type == NotificationType.MATCH_SCORE:
            requests.post(f"/tbans/match_score/{match_key}", data=data)
            return success_response
        elif notification_type == NotificationType.LEVEL_STARTING:
            requests.post(f"/tbans/event_level/{match_key}", data=data)
            return success_response
        elif notification_type == NotificationType.MATCH_VIDEO:
            requests.post(f"/tbans/match_video/{match_key}", data=data)
            return success_response

        return error_response

    # TODO: Need to handle district_points_updated here as well

    return error_response
