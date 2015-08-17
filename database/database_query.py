from google.appengine.api import memcache
from google.appengine.ext import ndb

import logging
from models.cached_query_result import CachedQueryResult


class DatabaseQuery(object):
    DATABASE_QUERY_VERSION = 0
    BASE_CACHE_KEY_FORMAT = "{}:{}:{}"  # (partial_cache_key, cache_version, database_query_version)

    def _render_cache_key(self, partial_cache_key):
        return self.BASE_CACHE_KEY_FORMAT.format(
            partial_cache_key,
            self.CACHE_VERSION,
            self.DATABASE_QUERY_VERSION)

    @property
    def cache_key(self):
        if not hasattr(self, '_cache_key'):
            self._cache_key = self._render_cache_key(self.CACHE_KEY_FORMAT.format(*self._query_args))
        return self._cache_key

    @classmethod
    def delete_cache_multi(cls, cache_keys):
        logging.info("Deleting db query cache keys: {}".format(cache_keys))
        ndb.delete_multi([ndb.Key(CachedQueryResult, cache_key) for cache_key in cache_keys])

    def fetch(self):
        return self.fetch_async().get_result()

    @ndb.tasklet
    def fetch_async(self):
        cached_query = yield CachedQueryResult.get_by_id_async(self.cache_key)
        if cached_query is None:
            memcache.incr(
                'database_query_misses:{}'.format(self.DATABASE_QUERY_VERSION),
                initial_value=0)
            query_result = yield self._query_async()
            yield CachedQueryResult(
                id=self.cache_key,
                result=query_result,
            ).put_async()
        else:
            memcache.incr(
                'database_query_hits:{}'.format(self.DATABASE_QUERY_VERSION),
                initial_value=0)
            query_result = cached_query.result

        raise ndb.Return(query_result)
