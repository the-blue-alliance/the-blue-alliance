from functools import partial, wraps

from flask import current_app, make_response, request, Response

from backend.common.environment import Environment


def cached_public(func=None, timeout: int = 61):
    if func is None:  # Handle no-argument decorator
        return partial(cached_public, timeout=timeout)

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if hasattr(current_app, "cache") and Environment.flask_response_cache_enabled():
            cached = current_app.cache.cached(
                timeout=timeout,
                response_filter=lambda resp: make_response(resp).status_code == 200,
            )
            resp = make_response(cached(func)(*args, **kwargs))
        else:
            resp = make_response(func(*args, **kwargs))
        if resp.status_code == 200:  # Only set cache headers for OK responses
            resp.headers["Cache-Control"] = "public, max-age={0}, s-maxage={0}".format(
                max(
                    timeout, 61
                )  # needs to be at least 61 seconds to work with Google Frontend cache
            )
            resp.add_etag()

            # Return 304 Not Modified if ETag matches
            if resp.headers.get("ETag", None) in str(request.if_none_match):
                return Response(status=304)

        return resp

    return decorated_function


def memoize(func=None, timeout: int = 61):
    if func is None:  # Handle no-argument decorator
        return partial(memoize, timeout=timeout)

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if hasattr(current_app, "cache"):
            cached = current_app.cache.memoize(timeout=timeout)
            return cached(func)(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return decorated_function
