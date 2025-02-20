import json
import logging

from flask import abort, Blueprint, Flask, jsonify, redirect, request, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.wrappers import Response

from backend.common.environment import Environment
from backend.common.memcache import MemcacheClient
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


def maybe_register(app: Flask, csrf: CSRFProtect) -> None:
    if Environment.is_dev():
        app.register_blueprint(local_routes)

        from backend.common.deferred import install_defer_routes

        install_defer_routes(app)

        # Since we only install this on devservers, CSRF isn't necessary
        csrf.exempt(local_routes)
