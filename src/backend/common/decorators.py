from datetime import timedelta
from functools import partial, wraps
from typing import Callable, Optional, Union

from flask import current_app, has_request_context, make_response, request, Response
from flask_caching import CachedResponse
from werkzeug.exceptions import NotFound

from backend.common.environment import Environment


def cached_public(
    func: Optional[Callable] = None,
    ttl: Union[int, timedelta] = 61,
    cache_redirects: bool = False,
    query_string: bool = True,
):
    """
    Caches the handler's response and marks it publicly cacheable.

    The cache is keyed on path (and query string by default unless query_string=False),
    with no user component, so the response body is stored once and served to every
    visitor. Never render anything session-specific - a CSRF token, account
    details, per-user state - into a response wrapped in this decorator.

    See src/backend/web/tests/cached_public_csrf_test.py, which enforces this
    for CSRF tokens, and
    https://github.com/the-blue-alliance/the-blue-alliance/issues/10495.
    """
    timeout = ttl if isinstance(ttl, int) else int(ttl.total_seconds())
    if func is None:  # Handle no-argument decorator
        return partial(
            cached_public,
            ttl=ttl,
            cache_redirects=cache_redirects,
            query_string=query_string,
        )

    @wraps(func)
    def decorated_function(*args, **kwargs):
        status_codes = [200, 301, 302, 404] if cache_redirects else [200, 404]

        @wraps(func)
        def func_wrapper(*func_args, **func_kwargs):
            try:
                rv = func(*func_args, **func_kwargs)
            except NotFound as e:
                rv = current_app.handle_user_exception(e)
            resp = make_response(rv)
            if resp.status_code == 404:
                resp.freeze()
                return CachedResponse(resp, 61)
            return rv

        if hasattr(current_app, "cache") and Environment.flask_response_cache_enabled():
            cached = current_app.cache.cached(
                timeout=timeout,
                response_filter=lambda resp: make_response(resp).status_code
                in status_codes,
                query_string=query_string,
            )
            resp = make_response(cached(func_wrapper)(*args, **kwargs))
        else:
            try:
                resp = make_response(func(*args, **kwargs))
            except NotFound as e:
                resp = make_response(current_app.handle_user_exception(e))
        if (
            resp.status_code in status_codes
            and Environment.cache_control_header_enabled()
        ):
            # Only set cache headers for cacheable responses
            browser_timeout = timeout
            if isinstance(resp, CachedResponse):
                browser_timeout = resp.timeout
            if resp.status_code == 404:
                browser_timeout = 61
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
