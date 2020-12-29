import logging

from flask import Flask
from flask_caching import Cache

from backend.common.redis import RedisClient


def configure_flask_cache(app: Flask) -> None:
    redis_client = RedisClient.get()
    if not redis_client:
        logging.warn(
            f"Unable to get redis client, not setting up flask cache for {app.import_name}"
        )
        config = {
            "CACHE_TYPE": "null",
        }
    else:
        logging.info("Setting up flask cache with redis client")
        config = {
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_HOST": redis_client,
        }
    cache = Cache(config=config)
    cache.init_app(app)
    app.cache = cache
