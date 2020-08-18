from urllib.parse import urljoin, urlparse

from flask import redirect, request
from werkzeug.wrappers import Response


def is_safe_url(target: str) -> bool:
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def safe_next_redirect(fallback_url: str) -> Response:
    next_response = redirect(fallback_url)
    next = request.args.get("next")
    if next and is_safe_url(next):
        next_response = redirect(next)
    return next_response
