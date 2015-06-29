from google.appengine.api import memcache
from google.appengine.ext import ndb

from models.cached_query_result import CachedQueryResult


class DatabaseQuery(object):
    DATABASE_QUERY_VERSION = 0

    def _get_cache_key(self):
        return "{}:{}:{}".format(
            self.CACHE_KEY_FORMAT.format(*self._query_args),
            self.CACHE_VERSION,
            self.DATABASE_QUERY_VERSION)

    @ndb.tasklet
    def fetch_async(self):
        cache_key = self._get_cache_key()

        cached_query = yield CachedQueryResult.get_by_id_async(cache_key)
        if cached_query is None:
            memcache.incr(
                'database_query_misses:{}'.format(self.DATABASE_QUERY_VERSION),
                initial_value=0)
            query_result = yield self._query_async()
            if query_result:
                yield CachedQueryResult(
                    id=cache_key,
                    result=query_result,
                ).put_async()
        else:
            memcache.incr(
                'database_query_hits:{}'.format(self.DATABASE_QUERY_VERSION),
                initial_value=0)
            query_result = cached_query.result

        raise ndb.Return(query_result)
