from flask import abort, Blueprint, Flask, redirect, request, url_for, make_response
from flask_wtf.csrf import CSRFProtect
from werkzeug.wrappers import Response

from backend.common.environment import Environment
from backend.common.sitevars.apiv3_key import Apiv3Key
from backend.web.local.bootstrap import LocalDataBootstrap
from backend.web.profiled_render import render_template
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify

from google.appengine.api import taskqueue

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
def bootstrap() -> Response:
    apiv3_key = Apiv3Key.api_key()
    template_values = {
        "apiv3_key": apiv3_key,
        "status": request.args.get("status"),
        "view_url": request.args.get("url"),
        "long_running": request.args.get("long_running"),
    }
    return render_template("local/bootstrap.html", template_values)


@local_routes.route("/bootstrap", methods=["POST"])
def bootstrap_post() -> Response:
    key = request.form.get("bootstrap_key", "")
    apiv3_key = request.form.get("apiv3_key") or Apiv3Key.api_key().strip()

    if not apiv3_key:
        return redirect(url_for(".bootstrap", status="bad_key"))

    # Verifies that the TBA key is usable in an obvious way.
    if not LocalDataBootstrap.verify_apiv3_key(apiv3_key):
        return redirect(url_for(".bootstrap", status="bad_apiv3"))

    return_url = None

    if key.isdigit():
        event_keys = [
            event["key"]
            for event in LocalDataBootstrap.fetch_endpoint(f"events/{key}", apiv3_key)
        ]

        for (
            event
        ) in (
            event_keys
        ):  # This avoids getting the last key if we don't already have it or we catch a retry.  Need to properly check if we get a bad response or something.
            taskqueue.add(
                url=url_for(".bootstrap_key"),
                method="GET",
                target="py3-tasks-io",
                queue_name="datafeed",
                params={"target_key": event, "apiv3_key": apiv3_key},
            )
    else:
        return_url = LocalDataBootstrap.bootstrap_key(key, apiv3_key)

    good = key.isdigit() or return_url is not None

    return redirect(
        url_for(
            ".bootstrap",
            status="success" if good else "bad_key",
            return_url=return_url,
            long_running=bool(key.isdigit()),
        )
    )

@local_routes.route("/bootstrap_key")
def bootstrap_key() -> Response:
    target_key= request.args.get("target_key")
    apiv3_key = request.args.get("apiv3_key")

    LocalDataBootstrap.bootstrap_key(target_key, apiv3_key)

    return make_response(profiled_jsonify({'OK':'Yes'}), 200)


@local_routes.route("/bootstrap_key")
def bootstrap_key() -> Response:
    target_key = request.args.get("target_key")
    apiv3_key = request.args.get("apiv3_key")

    LocalDataBootstrap.bootstrap_key(target_key, apiv3_key)

    return make_response(profiled_jsonify({"OK": "Yes"}), 200)


def maybe_register(app: Flask, csrf: CSRFProtect) -> None:
    if Environment.is_dev():
        app.register_blueprint(local_routes)

        # Since we only install this on devservers, CSRF isn't necessary
        csrf.exempt(local_routes)
