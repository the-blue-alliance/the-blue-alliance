import uuid

from flask import Blueprint, redirect, request, session, url_for
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.wrappers.response import Response

from backend.common.auth import current_user
from backend.common.consts.client_type import ClientType
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.account import Account
from backend.common.models.mobile_client import MobileClient
from backend.web.decorators import require_login
from backend.web.profiled_render import render_template

blueprint = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@blueprint.route("/add", methods=["GET"])
@require_login
def webhook_add() -> Response:
    template_values = {
        "error": session.pop("error", None),
    }

    return render_template("webhook_add.html", template_values)


@blueprint.route("/add", methods=["POST"])
@require_login
def webhook_add_post() -> Response:
    url = request.form.get("url")
    name = request.form.get("name")

    if not url or not name:
        session["error"] = 1
        return redirect(url_for(".webhook_add"))

    # Always generate secret server-side; previously allowed clients to set the secret
    secret = uuid.uuid4().hex

    user = none_throws(current_user())
    query = MobileClient.query(
        MobileClient.messaging_id == url,
        ancestor=user.account_key,
    )

    verification_key = TBANSHelper.verify_webhook(url, secret)
    if query.count() == 0:
        # Webhook doesn't exist, add it
        client = MobileClient(
            parent=user.account_key,
            user_id=str(user.uid),
            messaging_id=url,
            display_name=name,
            secret=secret,
            client_type=ClientType.WEBHOOK,
            verified=False,
            verification_code=verification_key,
        )
        client.put()
    else:
        # Webhook already exists. Update the secret and send new verification
        current = query.fetch()[0]
        current.secret = secret
        current.verification_code = verification_key
        current.verified = False
        current.put()

    return redirect(url_for("account.overview"))


@blueprint.route("/delete", methods=["POST"])
@require_login
def webhook_delete() -> Response:
    user = none_throws(current_user())

    client_id = request.form.get("client_id")
    if not client_id:
        return redirect(url_for("account.overview"))

    to_delete = ndb.Key(Account, user.uid, MobileClient, int(client_id))
    to_delete.delete()

    return redirect(url_for("account.overview"))


@blueprint.route("/verify/<int:client_id>", methods=["GET"])
@require_login
def webhook_verify(client_id) -> Response:
    template_values = {"error": session.pop("error", None), "client_id": client_id}

    return render_template("webhook_verify.html", template_values)


@blueprint.route("/verify/<int:client_id>", methods=["POST"])
@require_login
def webhook_verify_post(client_id) -> Response:
    user = none_throws(current_user())

    verification = request.form.get("code")
    if not verification:
        session["error"] = 1
        return redirect(url_for(".webhook_verify", client_id=client_id))

    webhook = MobileClient.get_by_id(client_id, parent=user.account_key)
    if (
        not webhook
        or webhook.client_type != ClientType.WEBHOOK
        or str(user.uid) != webhook.user_id
    ):
        return redirect(url_for("account.overview"))

    if verification == webhook.verification_code:
        webhook.verified = True
        webhook.put()
        return redirect(url_for("account.overview", webhook_verification_success=1))
    else:
        session["error"] = 1
        return redirect(url_for(".webhook_verify", client_id=client_id))


@blueprint.route("/send_verification", methods=["POST"])
@require_login
def webhook_send_verification() -> Response:
    user = none_throws(current_user())

    client_id = request.form.get("client_id")
    if not client_id:
        return redirect(url_for("account.overview"))

    webhook = MobileClient.get_by_id(int(client_id), parent=user.account_key)
    if (
        not webhook
        or webhook.client_type != ClientType.WEBHOOK
        or str(user.uid) != webhook.user_id
    ):
        return redirect(url_for("account.overview"))

    verification_key = TBANSHelper.verify_webhook(webhook.messaging_id, webhook.secret)

    webhook.verification_code = verification_key
    webhook.verified = False
    webhook.put()

    return redirect(url_for("account.overview"))
