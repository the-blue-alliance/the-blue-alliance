from flask import make_response
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
        return resp

    return decorated_function
