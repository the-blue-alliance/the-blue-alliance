The Blue Alliance uses [redis](https://redis.io/) to act as a fast cache for data that would be otherwise expensive to load. Examples of applications for redis are:
 - an [NDB global cache](https://googleapis.dev/python/python-ndb/latest/global_cache.html) implementation to reduce the number of queries that have to hit the backing datastore
 - storing rendered HTML output pages to avoid repetitive work
 - in local development mode, backing [https://github.com/the-blue-alliance/the-blue-alliance/wiki/Queues-and-defer#redis--rq](`rq`) to run task queues


The application shares a single redis connection (using the standard [library](https://pypi.org/project/redis/)) among all of these instances. This is managed by the `RedisClient` class, which reads the connection location from the `REDIS_CACHE_URL` environment variable. If this variable is unset, caching should be considered disabled.

### Using Redis

Redis exposes a standard Key-Value Store interface. The [redis-py](https://pypi.org/project/redis/) library has a quick getting started guide.

```python
from backend.common.redis import RedisClient
redis_client = RedisClient.get()
# if redis_client is None, then caching is disabled

redis_client.set('foo', 'bar')  # will return True
redis_client.get('foo')  # will return 'bar'
```

### Local Setup

The development container has a running instance of redis by default. It can be found running on `localhost:6379` (the default port). The URL for redis connection can be configured using the `redis_cache_url` field in the local property file.

### Production Setup

In production, we run managed redis [Google Cloud Memorystore](https://cloud.google.com/memorystore). The deploy process will configure the `REDIS_CACHE_URL` and other networking components to set up the connection.
