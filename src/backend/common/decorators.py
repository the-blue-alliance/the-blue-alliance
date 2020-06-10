from flask import request, make_response, Response
from functools import partial, wraps


def cached_public(func=None, timeout: int = 61):
    if func is None:  # Handle no-argument decorator
        return partial(cached_public, timeout=timeout)

    @wraps(func)
    def decorated_function(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.headers["Cache-Control"] = "public, max-age={0}, s-maxage={0}".format(
            max(
                timeout, 61
            )  # needs to be at least 61 seconds to work with Google Frontend cache
        )
        resp.add_etag()

        # Check for ETag caching
        if resp.headers.get("ETag", None) in str(request.if_none_match):
            resp = Response(status=304)

        return resp

    return decorated_function
