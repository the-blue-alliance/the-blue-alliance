import os

from flask import Blueprint, Flask

from backend.web.local.bootstrap import bootstrap_key

"""
These are special handlers that only get installed when running locally
and are used as dev/unit test helpers
"""

local_routes = Blueprint("local", __name__, url_prefix="/local")


@local_routes.route("/bootstrap/<key>")
def bootstrap(key: str) -> str:
    bootstrap_key(key)
    return key


def maybe_register(app: Flask) -> None:
    env = os.environ.get("GAE_ENV")
    if env == "localdev":
        app.register_blueprint(local_routes)
