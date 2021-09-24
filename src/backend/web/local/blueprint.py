import time

import requests
from flask import abort, Blueprint, Flask, jsonify, redirect, request, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.wrappers import Response

from backend.common.environment import Environment
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


@local_routes.route("/certs")
def certs() -> Response:
    certs = {
        "1": "-----BEGIN CERTIFICATE-----\nMIIDYTCCAkmgAwIBAgIULae0OluSv2DbeUa8xfrHzBujSiAwDQYJKoZIhvcNAQEL\nBQAwKzEpMCcGA1UEAwwgdGVzdC5hcHBzcG90LmdzZXJ2aWNlYWNjb3VudC5jb20w\nIBcNMjEwOTI0MDIxNTAxWhgPOTk5OTEyMzEwMDAwMDBaMCsxKTAnBgNVBAMMIHRl\nc3QuYXBwc3BvdC5nc2VydmljZWFjY291bnQuY29tMIIBIjANBgkqhkiG9w0BAQEF\nAAOCAQ8AMIIBCgKCAQEAokZw4SrVbUv12ZMCie/fZeyvfGxui2jAAe1V5DINXHuu\nwrXrTMksqHK2bRoVaCR3ghi2r5qmS5ppMTEASceSTY6ZAqOJ5H5+1rXIqok9v+lY\ny3vZI2iwYit6jPCe7qslj3VMMut/fuJqrjRfMJzD/ZKzHJ+PibFuN8rEu5Vc87w3\n8frMDJMXZQ6utXLVWxbPWFryI2aLVLYPSHRiuYHtlcX5z+kqukxhObbl+MBthv2+\nmnQWgNCk0MR1hNkppyIFLIjxVZtM2ehuGxtCjd0EIbVFmcpuxCNjwW/1qhegIwtK\nWKKu8hdAws4p3aZACr5zyUIiDn9i7DB5mYTFFUnl3wIDAQABo3sweTAJBgNVHRME\nAjAAMCwGCWCGSAGG+EIBDQQfFh1PcGVuU1NMIEdlbmVyYXRlZCBDZXJ0aWZpY2F0\nZTAdBgNVHQ4EFgQUJcoH+5oRWYmw0HlAa3mWkuCzXTIwHwYDVR0jBBgwFoAUJcoH\n+5oRWYmw0HlAa3mWkuCzXTIwDQYJKoZIhvcNAQELBQADggEBAALtSKIY9j+1tsg9\nSe5R74gpZQrPXhzN9NwTLyaWC2fOlqdBojojk+fMmfxTEi/6GsOSu76V64bdniJc\nW2VXS4e+YikG8jZa3jQd4sbCkyTvtMpRB3it2rPE9frLfFPlNNQe8s0uQ1qFdQCd\njUsQ4VUU5+gbmtEEFPM1zKJryE2Z9Ho+6lOOGhLk1bkPImWwaYV01Ky4ZZzbY7/m\nkNkwyugp7grXvLUJyC+kgBRZcI6NirUnqhjym6N1LuOiK5PHl0xogwq48xCYIn5n\nsg+tAgae5drfqSv2R44Qv40c7QfWhYEibOvGLOwdEHFxPKeQCOjMnnxCZAMR69ex\n6xIwD6A=\n-----END CERTIFICATE-----",
    }
    return jsonify(certs)


@local_routes.route("/token", methods=["POST"])
def id_token() -> Response:
    assertion = request.form.get("assertion")
    grant_type = request.form.get("grant_type")

    if not assertion or not grant_type:
        return jsonify({
            "error": "invalid_grant",
            "error_description": repr(e)
        }), 400

    # certs_response = requests.get("http://localhost:8080" + url_for(".certs"))
    # certs = certs_response.json()

    certs = {
        "1": "-----BEGIN CERTIFICATE-----\nMIIDYTCCAkmgAwIBAgIULae0OluSv2DbeUa8xfrHzBujSiAwDQYJKoZIhvcNAQEL\nBQAwKzEpMCcGA1UEAwwgdGVzdC5hcHBzcG90LmdzZXJ2aWNlYWNjb3VudC5jb20w\nIBcNMjEwOTI0MDIxNTAxWhgPOTk5OTEyMzEwMDAwMDBaMCsxKTAnBgNVBAMMIHRl\nc3QuYXBwc3BvdC5nc2VydmljZWFjY291bnQuY29tMIIBIjANBgkqhkiG9w0BAQEF\nAAOCAQ8AMIIBCgKCAQEAokZw4SrVbUv12ZMCie/fZeyvfGxui2jAAe1V5DINXHuu\nwrXrTMksqHK2bRoVaCR3ghi2r5qmS5ppMTEASceSTY6ZAqOJ5H5+1rXIqok9v+lY\ny3vZI2iwYit6jPCe7qslj3VMMut/fuJqrjRfMJzD/ZKzHJ+PibFuN8rEu5Vc87w3\n8frMDJMXZQ6utXLVWxbPWFryI2aLVLYPSHRiuYHtlcX5z+kqukxhObbl+MBthv2+\nmnQWgNCk0MR1hNkppyIFLIjxVZtM2ehuGxtCjd0EIbVFmcpuxCNjwW/1qhegIwtK\nWKKu8hdAws4p3aZACr5zyUIiDn9i7DB5mYTFFUnl3wIDAQABo3sweTAJBgNVHRME\nAjAAMCwGCWCGSAGG+EIBDQQfFh1PcGVuU1NMIEdlbmVyYXRlZCBDZXJ0aWZpY2F0\nZTAdBgNVHQ4EFgQUJcoH+5oRWYmw0HlAa3mWkuCzXTIwHwYDVR0jBBgwFoAUJcoH\n+5oRWYmw0HlAa3mWkuCzXTIwDQYJKoZIhvcNAQELBQADggEBAALtSKIY9j+1tsg9\nSe5R74gpZQrPXhzN9NwTLyaWC2fOlqdBojojk+fMmfxTEi/6GsOSu76V64bdniJc\nW2VXS4e+YikG8jZa3jQd4sbCkyTvtMpRB3it2rPE9frLfFPlNNQe8s0uQ1qFdQCd\njUsQ4VUU5+gbmtEEFPM1zKJryE2Z9Ho+6lOOGhLk1bkPImWwaYV01Ky4ZZzbY7/m\nkNkwyugp7grXvLUJyC+kgBRZcI6NirUnqhjym6N1LuOiK5PHl0xogwq48xCYIn5n\nsg+tAgae5drfqSv2R44Qv40c7QfWhYEibOvGLOwdEHFxPKeQCOjMnnxCZAMR69ex\n6xIwD6A=\n-----END CERTIFICATE-----",
    }

    try:
        from google.auth import jwt

        info = jwt.decode(assertion, certs=certs)
    except Exception as e:
        return jsonify({
            "error": "invalid_grant",
            "error_description": repr(e)
        }), 400

    aud = info.get("aud")
    if aud != "http://localhost:8080/local/token":
        return jsonify({
            "error": "invalid_aud",
            "error_description": "Invalid audience for token"
        }), 400

    iss = info.get("iss")
    if iss != "test@appspot.gserviceaccount.com":
        return jsonify({
            "error": "invalid_iss",
            "error_description": "Invalid issuer for token"
        }), 400

    iat = info.get("iat")
    if not iat:
        return jsonify({
            "error": "invalid_iss",
            "error_description": "Missing issued at for token"
        }), 400

    exp = info.get("exp")
    if not exp:
        return jsonify({
            "error": "invalid_iss",
            "error_description": "Missing expiration for token"
        }), 400

    expires_in = exp - iat
    if expires_in <= 0:
        return jsonify({
            "error": "expired_token",
            "error_description": "Token has expired"
        }), 400

    epoch_time = int(time.time())
    until_exp = exp - epoch_time
    if until_exp <= 0:
        return jsonify({
            "error": "expired_token",
            "error_description": "Token has expired"
        }), 400

    return jsonify({"id_token": assertion, "expires_in": expires_in, "token_type": "bearer"})


def maybe_register(app: Flask, csrf: CSRFProtect) -> None:
    if Environment.is_dev():
        app.register_blueprint(local_routes)

        # Since we only install this on devservers, CSRF isn't necessary
        csrf.exempt(local_routes)
