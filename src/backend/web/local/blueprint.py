import json
import logging
import random
import string

from flask import (
    abort,
    Blueprint,
    Flask,
    jsonify,
    make_response,
    redirect,
    request,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.environment import Environment
from backend.common.helpers.fms_companion_helper import FMSCompanionHelper
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.memcache import MemcacheClient
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.sitevars.apiv3_key import Apiv3Key
from backend.web.local.bootstrap import LocalDataBootstrap
from backend.web.profiled_render import render_template

"""
These are special handlers that only get installed when running locally
and are used as dev/unit test helpers
"""

local_routes = Blueprint("local", __name__, url_prefix="/local")


@local_routes.before_request
def before_request() -> None:
    # Fail if we're not running in dev mode, as a sanity check
    if not Environment.is_dev():
        abort(403)


@local_routes.route("/bootstrap", methods=["GET"])
def bootstrap() -> str:
    apiv3_key = Apiv3Key.api_key()
    template_values = {
        "apiv3_key": apiv3_key,
        "status": request.args.get("status"),
        "view_url": request.args.get("url"),
    }
    return render_template("local/bootstrap.html", template_values)


@local_routes.route("/bootstrap", methods=["POST"])
def bootstrap_post() -> Response:
    key = request.form.get("bootstrap_key", "")
    apiv3_key = request.form.get("apiv3_key") or Apiv3Key.api_key()

    if not apiv3_key:
        return redirect(url_for(".bootstrap", status="bad_apiv3"))

    return_url = LocalDataBootstrap.bootstrap_key(key, apiv3_key)
    return redirect(
        url_for(
            ".bootstrap",
            status="success" if return_url is not None else "bad_key",
            url=return_url,
        )
    )


@local_routes.route("/sdk_version")
def sdk_version() -> str:
    with open("/usr/lib/google-cloud-sdk/VERSION", "r") as version_file:
        return version_file.read()


@local_routes.route("/webhooks", methods=["POST"])
def webhook_server_post() -> str:
    incoming_webhook = request.json
    logging.info(f"got webhook: {incoming_webhook}")

    cache = MemcacheClient.get()
    cache.set(b"test_webhooks_received", json.dumps(incoming_webhook))

    return ""


@local_routes.route("/webhooks", methods=["GET"])
def webhook_server_get() -> Response:
    cache = MemcacheClient.get()
    webhooks = cache.get(b"test_webhooks_received") or "{}"
    cache.delete(b"test_webhooks_received")
    return jsonify(json.loads(webhooks))


@local_routes.route("/get_fms_companion_db/<string:event_key>", methods=["GET"])
def get_fms_companion_db(event_key: str) -> Response:
    file_contents = FMSCompanionHelper.read_newest_companion_db(event_key)
    if file_contents is None:
        return make_response(
            jsonify({"Error": f"No companion database found for event {event_key}"}),
            404,
        )

    response = make_response(file_contents)
    response.headers["Content-Type"] = "application/x-sqlite3"
    response.headers["Content-Disposition"] = (
        f"attachment; filename={f'{event_key}_companion.db'}"
    )
    return response


@local_routes.route("/create_test_event/<string:event_key>", methods=["POST"])
def create_test_event(event_key: str) -> Response:
    # Validate event key format
    if not Event.validate_key_name(event_key):
        return make_response(
            jsonify({"Error": "Invalid event key format."}),
            400,
        )

    # Parse event key to get year and event_short
    year_str = event_key[:4]
    year = int(year_str)
    event_short = event_key[4:]

    # Check if event already exists
    event = Event.get_by_id(event_key)
    if event:
        # Check if auth already exists
        existing_auth = ApiAuthAccess.query(ApiAuthAccess.event_list == event.key).get()
        if existing_auth:
            return jsonify(
                {
                    "Success": f"Event {event_key} already exists",
                    "event_key": event_key,
                    "auth_id": existing_auth.key.id(),
                    "auth_secret": existing_auth.secret,
                }
            )
    else:
        # Create new offseason event
        event = Event(
            id=event_key,
            year=year,
            event_short=event_short,
            event_type_enum=EventType.OFFSEASON,
            name=f"{year} {event_short.upper()} Test Event",
            short_name=f"{event_short.upper()} Test",
            official=False,
        )

        event = EventManipulator.createOrUpdate(event)

    # Generate auth credentials with all write permissions
    # Auth ID format: 16 character alphanumeric string
    auth_id = "".join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(16)
    )
    # Auth secret format: 64 character alphanumeric string
    auth_secret = "".join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(64)
    )

    # Get all write auth types (excluding READ_API)
    all_write_auth_types = [
        auth_type for auth_type in AuthType if auth_type != AuthType.READ_API
    ]

    auth = ApiAuthAccess(
        id=auth_id,
        secret=auth_secret,
        description=f"Auto-generated auth for test event {event_key}",
        event_list=[event.key],
        auth_types_enum=all_write_auth_types,
    )
    auth.put()

    return jsonify(
        {
            "Success": f"Event {event_key} created",
            "event_key": event_key,
            "auth_id": auth_id,
            "auth_secret": auth_secret,
        }
    )


def maybe_register(app: Flask, csrf: CSRFProtect) -> None:
    if Environment.is_dev():
        app.register_blueprint(local_routes)

        from backend.common.deferred import install_defer_routes

        install_defer_routes(app)

        # Since we only install this on devservers, CSRF isn't necessary
        csrf.exempt(local_routes)
