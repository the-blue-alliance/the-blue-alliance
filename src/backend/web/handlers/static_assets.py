import mimetypes

from flask import abort, redirect
from werkzeug.wrappers.response import Response

from backend.web.static_assets import (
    asset_content_hash,
    built_asset_path,
    static_asset_url,
)

ONE_YEAR_SECONDS = 365 * 24 * 60 * 60


def static_asset(content_hash: str, kind: str, filename: str) -> Response:
    asset = f"{kind}/{filename}"
    current_hash = asset_content_hash(asset)
    path = built_asset_path(asset)
    if current_hash is None or path is None:
        abort(404)

    if content_hash != current_hash:
        # Stale page or mid-deploy: never let a cache pin the wrong file to this URL
        response = redirect(static_asset_url(asset))
        response.headers["Cache-Control"] = "no-store"
        return response

    with open(path, "rb") as f:
        body = f.read()
    response = Response(body, mimetype=mimetypes.guess_type(path)[0])
    response.headers["Cache-Control"] = f"public, max-age={ONE_YEAR_SECONDS}, immutable"
    return response
