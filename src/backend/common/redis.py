import os
from typing import Optional

import redis
from pyre_extensions import none_throws


class RedisClient:
    """
    This will let us share redis clients across use cases in the code
    """

    client: Optional[redis.Redis] = None

    @classmethod
    def get(cls) -> Optional[redis.Redis]:
        redis_url = os.environ.get("REDIS_CACHE_URL")
        if not redis_url:
            return None

        if cls.client is None:
            cls.client = redis.Redis.from_url(redis_url)

        return none_throws(cls.client)
