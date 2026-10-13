import gzip
from typing import FrozenSet, Optional

from flask import Flask, request, Response

DEFAULT_MIN_SIZE = 500
DEFAULT_LEVEL = 6

COMPRESSIBLE_MIMETYPES: FrozenSet[str] = frozenset(
    {
        "application/javascript",
        "application/json",
        "application/manifest+json",
        "application/xml",
        "image/svg+xml",
        "text/css",
        "text/csv",
        "text/html",
        "text/javascript",
        "text/plain",
        "text/xml",
    }
)


def configure_gzip(
    app: Flask,
    min_size: int = DEFAULT_MIN_SIZE,
    level: int = DEFAULT_LEVEL,
    mimetypes: Optional[FrozenSet[str]] = None,
) -> None:
    compressible = mimetypes if mimetypes is not None else COMPRESSIBLE_MIMETYPES

    @app.after_request
    def compress_response(response: Response) -> Response:
        if response.status_code in (204, 304):
            return response
        if "Content-Encoding" in response.headers:
            return response
        if "no-transform" in response.headers.get("Cache-Control", ""):
            return response
        if response.direct_passthrough:
            return response
        if response.mimetype not in compressible:
            return response
        if request.accept_encodings.quality("gzip") <= 0:
            return response

        data = response.get_data()
        if len(data) < min_size:
            return response

        response.set_data(gzip.compress(data, compresslevel=level))
        response.headers["Content-Encoding"] = "gzip"
        response.vary.add("Accept-Encoding")

        # The bytes changed, so a strong ETag on the original body is no
        # longer valid. Weaken it instead of dropping it so conditional
        # requests (If-None-Match, weakly compared per RFC 9110) keep working.
        etag = response.headers.get("ETag")
        if etag is not None and not etag.startswith("W/"):
            response.headers["ETag"] = f"W/{etag}"

        return response
