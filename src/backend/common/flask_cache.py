import logging
import zlib
from typing import Any, Dict, Optional

from flask import Flask
from flask_caching import Cache
from flask_caching.backends.rediscache import BaseCache, RedisCache

from backend.common.redis import RedisClient


class CompressedRedisCache(RedisCache):
    def dump_object(self, value: Any) -> bytes:
        ret = super().dump_object(value)
        return zlib.compress(ret)

    def load_object(self, value: Optional[bytes]) -> Any:
        if value is None:
            return None
        decompressed = zlib.decompress(value)
        return super().load_object(decompressed)


def compressed_redis(app: Flask, config: Dict, args, kwargs) -> BaseCache:
    try:
        from redis import from_url as redis_from_url
    except ImportError:
        raise RuntimeError("no redis module found")

    kwargs.update(
        dict(
            host=config.get("CACHE_REDIS_HOST", "localhost"),
            port=config.get("CACHE_REDIS_PORT", 6379),
        )
    )
    password = config.get("CACHE_REDIS_PASSWORD")
    if password:
        kwargs["password"] = password

    key_prefix = config.get("CACHE_KEY_PREFIX")
    if key_prefix:
        kwargs["key_prefix"] = key_prefix

    db_number = config.get("CACHE_REDIS_DB")
    if db_number:
        kwargs["db"] = db_number

    redis_url = config.get("CACHE_REDIS_URL")
    if redis_url:
        kwargs["host"] = redis_from_url(redis_url, db=kwargs.pop("db", None))
    return CompressedRedisCache(*args, **kwargs)


def configure_flask_cache(app: Flask) -> None:
    redis_client = RedisClient.get()
    if not redis_client:
        logging.warning(
            f"Unable to get redis client, not setting up flask cache for {app.import_name}"
        )
        config = {
            "CACHE_TYPE": "null",
        }
    else:
        logging.info("Setting up flask cache with redis client")
        config = {
            "CACHE_TYPE": "backend.common.flask_cache.compressed_redis",
            "CACHE_REDIS_HOST": redis_client,
        }
    cache = Cache(config=config)
    cache.init_app(app)
    app.cache = cache
