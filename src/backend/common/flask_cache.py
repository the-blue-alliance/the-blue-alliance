import logging
from datetime import timedelta
from typing import Any, Dict

from flask import Flask, make_response, Response
from flask_caching import BaseCache, Cache, CachedResponse
from google.appengine.api import memcache

from backend.common.cache.flask_response_cache import MemcacheFlaskResponseCache


def app_engine_cache(_app: Flask, _config: Dict, *args, **kwargs) -> BaseCache:
    return MemcacheFlaskResponseCache(memcache.Client())


def configure_flask_cache(app: Flask) -> None:
    logging.info("Setting up flask cache with client")
    config = {
        "CACHE_TYPE": "backend.common.flask_cache.app_engine_cache",
    }
    cache = Cache(config=config)
    cache.init_app(app)
    app.cache = cache


def make_cached_response(*args: Any, ttl: timedelta) -> Response:
    resp = make_response(*args)
    return CachedResponse(response=resp, timeout=int(ttl.total_seconds()))
