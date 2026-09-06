import hashlib
import logging
import time
from datetime import timedelta
from functools import partial, wraps
from typing import Any, Callable, Optional, Union

from flask import current_app, g, has_request_context, make_response, request, Response
from flask_caching import CachedResponse

from backend.common.environment import Environment
from backend.common.memcache import MemcacheClient
from backend.common.profiler import Span

DEPS_METADATA_TTL: int = 86400  # 1 day (in seconds)


def _matches_etag(if_none_match: Any, etag: Optional[str]) -> bool:
    if not if_none_match or not etag:
        return False
    if hasattr(if_none_match, "contains_weak"):
        return if_none_match.contains_weak(etag) or bool(
            getattr(if_none_match, "star", False)
        )
    if hasattr(if_none_match, "contains"):
        return if_none_match.contains(etag) or bool(
            getattr(if_none_match, "star", False)
        )
    s = str(if_none_match)
    return etag in s or etag.strip('"') in s or "*" in s


def cached_public(
    func: Optional[Callable] = None,
    ttl: Union[int, timedelta] = 61,
    cache_redirects: bool = False,
):
    """
    Caches the handler's response and marks it publicly cacheable.

    The cache is keyed on path + query string only, with no user component, so
    the response body is stored once and served to every visitor. Never render
    anything session-specific - a CSRF token, account details, per-user state -
    into a response wrapped in this decorator.

    See src/backend/web/tests/cached_public_csrf_test.py, which enforces this
    for CSRF tokens, and
    https://github.com/the-blue-alliance/the-blue-alliance/issues/10495.
    """
    timeout = ttl if isinstance(ttl, int) else int(ttl.total_seconds())
    if func is None:  # Handle no-argument decorator
        return partial(cached_public, ttl=ttl, cache_redirects=cache_redirects)

    @wraps(func)
    def decorated_function(*args, **kwargs):
        status_codes = [200, 301, 302] if cache_redirects else [200]
        response_cache_enabled = (
            hasattr(current_app, "cache") and Environment.flask_response_cache_enabled()
        )

        cached = None
        cache_key = None
        if response_cache_enabled:
            cached = current_app.cache.cached(
                timeout=timeout,
                response_filter=lambda resp: make_response(resp).status_code
                in status_codes,
                query_string=True,
            )(func)
            try:
                cache_key = cached.make_cache_key(*args, use_request=True, **kwargs)
            except Exception as e:
                logging.warning(f"Failed to generate cache_key in cached_public: {e}")

        # Fast-path 304 check via Multi-Key Generation Vectors
        if (
            response_cache_enabled
            and cache_key
            and request.method in ("GET", "HEAD")
            and request.if_none_match
        ):
            try:
                meta = current_app.cache.get(f"deps:{cache_key}")
                if meta and isinstance(meta, dict):
                    expected_etag = meta.get("etag")
                    deps = meta.get("deps", [])
                    tokens = meta.get("tokens", {})
                    if expected_etag and _matches_etag(
                        request.if_none_match, expected_etag
                    ):
                        with Span("cached_public_fast_304"):
                            mc = MemcacheClient.get()
                            gen_keys = [f"gen:{k}".encode() for k in deps]
                            current_gens = mc.get_multi(gen_keys) if gen_keys else {}
                            match = True
                            for k in deps:
                                gen_k = f"gen:{k}".encode()
                                if current_gens.get(gen_k) != tokens.get(k):
                                    match = False
                                    break
                            if match:
                                browser_timeout = meta.get("timeout", timeout)
                                cache_control = (
                                    "public, max-age={0}, s-maxage={0}".format(
                                        max(browser_timeout, 61)
                                    )
                                )
                                return Response(
                                    status=304,
                                    headers={
                                        "ETag": expected_etag,
                                        "Cache-Control": cache_control,
                                    },
                                )
                            else:
                                # Data has changed! Invalidate cached view response and metadata
                                current_app.cache.delete(cache_key)
                                current_app.cache.delete(f"deps:{cache_key}")
            except Exception as e:
                logging.warning(f"Error during fast 304 generation check: {e}")

        if response_cache_enabled and cached is not None:
            resp = make_response(cached(*args, **kwargs))
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

            # Check if accessed query keys were registered during request execution
            accessed_keys = sorted(getattr(g, "accessed_query_keys", set()))
            if accessed_keys and response_cache_enabled and cache_key:
                try:
                    mc = MemcacheClient.get()
                    gen_keys = [f"gen:{k}".encode() for k in accessed_keys]
                    tokens_by_gen_key = mc.get_multi(gen_keys)
                    tokens_by_query_key = {}
                    keys_to_init = {}
                    now_ts = int(time.time())
                    for k in accessed_keys:
                        gen_k = f"gen:{k}".encode()
                        tok = tokens_by_gen_key.get(gen_k)
                        if tok is None:
                            tok = now_ts
                            keys_to_init[gen_k] = now_ts
                        tokens_by_query_key[k] = tok

                    if keys_to_init:
                        mc.set_multi(keys_to_init)

                    content_bytes = resp.get_data()
                    content_md5 = hashlib.md5(content_bytes).hexdigest()
                    composite_str = ";".join(
                        f"{k}={tokens_by_query_key[k]}" for k in accessed_keys
                    )
                    composite_etag = (
                        f'"{hashlib.md5(f"{content_md5}:{composite_str}".encode()).hexdigest()}"'
                    )
                    resp.headers["ETag"] = composite_etag

                    meta = {
                        "etag": composite_etag,
                        "deps": accessed_keys,
                        "tokens": tokens_by_query_key,
                        "timeout": browser_timeout,
                    }
                    current_app.cache.set(
                        f"deps:{cache_key}", meta, timeout=DEPS_METADATA_TTL
                    )
                except Exception as e:
                    logging.warning(
                        f"Failed to record multi-key generation metadata: {e}"
                    )
                    if "ETag" not in resp.headers:
                        resp.add_etag()
            else:
                # If cached response already has an ETag or metadata has an ETag, preserve it
                if response_cache_enabled and cache_key:
                    meta = current_app.cache.get(f"deps:{cache_key}")
                    if meta and isinstance(meta, dict) and "etag" in meta:
                        resp.headers["ETag"] = meta["etag"]
                    elif "ETag" not in resp.headers:
                        resp.add_etag()
                elif "ETag" not in resp.headers:
                    resp.add_etag()

            # Return 304 Not Modified if ETag matches
            etag = resp.headers.get("ETag", None)
            if etag and _matches_etag(request.if_none_match, etag):
                return Response(status=304, headers=resp.headers)

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
