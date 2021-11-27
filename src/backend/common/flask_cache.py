import logging
from typing import Dict

from flask import Flask
from flask_caching import BaseCache, Cache
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
