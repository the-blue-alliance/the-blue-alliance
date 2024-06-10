from datetime import timedelta
from functools import partial, wraps
from typing import Callable, Optional, Union

from flask import current_app, has_request_context, make_response, request, Response
from flask_caching import CachedResponse

from backend.common.environment import Environment


def cached_public(
    func: Optional[Callable] = None,
    ttl: Union[int, timedelta] = 61,
    cache_redirects: bool = False,
):
    timeout = ttl if isinstance(ttl, int) else int(ttl.total_seconds())
    if func is None:  # Handle no-argument decorator
        return partial(cached_public, ttl=ttl, cache_redirects=cache_redirects)

    @wraps(func)
    def decorated_function(*args, **kwargs):
        status_codes = [200, 301, 302] if cache_redirects else [200]

        if hasattr(current_app, "cache") and Environment.flask_response_cache_enabled():
            cached = current_app.cache.cached(
                timeout=timeout,
                response_filter=lambda resp: make_response(resp).status_code
                in status_codes,
                query_string=True,
            )
            resp = make_response(cached(func)(*args, **kwargs))
        else:
            resp = make_response(func(*args, **kwargs))
        if (
            resp.status_code in status_codes
            and Environment.cache_control_header_enabled()
        ):
            # Only set cache headers for OK responses
            browser_timeout = timeout
            if isinstance(resp, CachedResponse):
                browser_timeout = resp.timeout
            resp.headers["Cache-Control"] = "public, max-age={0}, s-maxage={0}".format(
                max(
                    browser_timeout, 61
                )  # needs to be at least 61 seconds to work with Google Frontend cache
            )
            resp.add_etag()

            # Return 304 Not Modified if ETag matches
            if resp.headers.get("ETag", None) in str(request.if_none_match):
                return Response(status=304)

            if request.if_modified_since is not None and resp.last_modified is not None:
                if request.if_modified_since >= resp.last_modified:
                    return Response(status=304)

        return resp

    return decorated_function


def memoize(func: Optional[Callable] = None, timeout: int = 61):
    if func is None:  # Handle no-argument decorator
        return partial(memoize, timeout=timeout)

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if has_request_context() and hasattr(current_app, "cache"):
            cached = current_app.cache.memoize(timeout=timeout)
            return cached(func)(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return decorated_function
