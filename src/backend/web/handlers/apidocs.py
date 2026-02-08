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
    from backend.common.consts.client_type import ClientType
    from backend.common.models.mobile_client import MobileClient

    user = current_user()
    webhooks = []
    if user:
        webhooks = MobileClient.query(
            MobileClient.user_id == str(user.uid),
            MobileClient.client_type == ClientType.WEBHOOK,
            MobileClient.verified == True,
        ).fetch()

    template_values = {
        "enabled": ENABLED_NOTIFICATIONS,
        "types": NOTIFICATION_TYPES,
        "webhooks": webhooks,
    }
    return render_template("apidocs_webhooks.html", template_values)


@blueprint.route("/webhooks/test/<int:type>", methods=["POST"])
@enforce_login
def apidocs_webhooks_notification(type: int) -> Response:
    event_key = request.form.get("event_key")
    team_key = request.form.get("team_key")
    match_key = request.form.get("match_key")
    district_key = request.form.get("district_key")
    webhook_client_id = request.form.get("webhook_client_id")

    user = none_throws(current_user())
    user_id = str(user.uid)

    def error_response(message: str):
        return make_response(jsonify({"Error": message}), 400)

    try:
        notification_type = NotificationType(type)
    except ValueError:
        return error_response("Invalid notification type")

    if not webhook_client_id:
        return error_response("Webhook not specified")

    from backend.common.consts.client_type import ClientType
    from backend.common.models.mobile_client import MobileClient

    webhook = MobileClient.get_by_id(int(webhook_client_id), parent=user.account_key)
    if not webhook:
        return error_response("Webhook not found")
    if webhook.client_type != ClientType.WEBHOOK:
        return error_response("Client is not a webhook")
    if webhook.user_id != user_id:
        return error_response("Webhook does not belong to current user")
    if not webhook.verified:
        return error_response("Webhook is not verified")

    success = TBANSHelper.send_webhook_test(
        webhook,
        notification_type,
        event_key=event_key,
        team_key=team_key,
        match_key=match_key,
        district_key=district_key,
    )
    if success:
        return make_response("ok", 200)
    else:
        return error_response("Failed to send notification to webhook")
