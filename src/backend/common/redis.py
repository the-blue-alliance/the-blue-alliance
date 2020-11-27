from typing import Optional

import redis
from pyre_extensions import none_throws

from backend.common.environment import Environment


class RedisClient:
    """
    This will let us share redis clients across use cases in the code
    """

    _client: Optional[redis.Redis] = None

    @classmethod
    def get(cls) -> Optional[redis.Redis]:
        redis_url = Environment.redis_url()
        if not redis_url:
            return None

        if cls._client is None:
            cls._client = redis.Redis.from_url(redis_url)

        return none_throws(cls._client)

    @classmethod
    def reset(cls) -> None:
        cls._client = None
