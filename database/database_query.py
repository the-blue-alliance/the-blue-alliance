import datetime
from google.appengine.api import memcache
from google.appengine.ext import ndb

import logging
from models.cached_query_result import CachedQueryResult
import random
from stackdriver.profiler import TraceContext
import tba_config

MEMCACHE_CLIENT = memcache.Client()


class DatabaseQuery(object):
    DATABASE_QUERY_VERSION = 4
    DATABASE_HITS_MEMCACHE_KEYS = ['database_query_hits_{}:{}'.format(i, DATABASE_QUERY_VERSION) for i in range(25)]
    DATABASE_MISSES_MEMCACHE_KEYS = ['database_query_misses_{}:{}'.format(i, DATABASE_QUERY_VERSION) for i in range(25)]
    BASE_CACHE_KEY_FORMAT = "{}:{}:{}"  # (partial_cache_key, cache_version, database_query_version)
    VALID_DICT_VERSIONS = {3}
    DICT_CONVERTER = None

    def __init__(self, *args):
        self._query_args = args

    @property
    def cache_key(self):
        if not hasattr(self, '_cache_key'):
            self._cache_key = self.BASE_CACHE_KEY_FORMAT.format(
                self.CACHE_KEY_FORMAT.format(*self._query_args),
                self.CACHE_VERSION,
                self.DATABASE_QUERY_VERSION)

        return self._cache_key

    @classmethod
    def delete_cache_multi(cls, cache_keys):
        all_cache_keys = []
        for cache_key in cache_keys:
            all_cache_keys.append(cache_key)
            if cls.DICT_CONVERTER is not None:
                all_cache_keys += [cls._dict_cache_key(cache_key, valid_dict_version) for valid_dict_version in cls.VALID_DICT_VERSIONS]
        logging.info("Deleting db query cache keys: {}".format(all_cache_keys))
        ndb.delete_multi([ndb.Key(CachedQueryResult, cache_key) for cache_key in all_cache_keys])

    @classmethod
    def _dict_cache_key(cls, cache_key, dict_version):
        return '{}~dictv{}.{}'.format(cache_key, dict_version, cls.DICT_CONVERTER.SUBVERSIONS[dict_version])

    def fetch(self, dict_version=None, return_updated=False):
        return self.fetch_async(
            dict_version=dict_version,
            return_updated=return_updated).get_result()

    @ndb.tasklet
    def fetch_async(self, dict_version=None, return_updated=False):
        with TraceContext() as root:
            with root.span("{}.fetch_async".format(self.__class__.__name__)):
                if dict_version:
                    if dict_version not in self.VALID_DICT_VERSIONS:
                        raise Exception("Bad api version for database query: {}".format(dict_version))
                    cache_key = self._dict_cache_key(self.cache_key, dict_version)
                else:
                    cache_key = self.cache_key

                cached_query = yield CachedQueryResult.get_by_id_async(cache_key)
                do_stats = random.random() < tba_config.RECORD_FRACTION
                rpcs = []
                if cached_query is None:
                    if do_stats:
                        rpcs.append(MEMCACHE_CLIENT.incr_async(
                            random.choice(self.DATABASE_MISSES_MEMCACHE_KEYS),
                            initial_value=0))
                    query_result = yield self._query_async()
                    if dict_version:
                        query_result = self.DICT_CONVERTER.convert(query_result, dict_version)
                    if tba_config.CONFIG['database_query_cache']:
                        if dict_version:
                            rpcs.append(CachedQueryResult(
                                id=cache_key,
                                result_dict=query_result,
                            ).put_async())
                        else:
                            rpcs.append(CachedQueryResult(
                                id=cache_key,
                                result=query_result,
                            ).put_async())
                    updated = datetime.datetime.now()
                else:
                    if do_stats:
                        rpcs.append(MEMCACHE_CLIENT.incr_async(
                            random.choice(self.DATABASE_HITS_MEMCACHE_KEYS),
                            initial_value=0))
                    if dict_version:
                        query_result = cached_query.result_dict
                    else:
                        query_result = cached_query.result
                    updated = cached_query.updated

                for rpc in rpcs:
                    try:
                        rpc.get_result()
                    except Exception, e:
                        logging.warning("An RPC in DatabaseQuery.fetch_async() failed!")
                if return_updated:
                    raise ndb.Return((query_result, updated))
                else:
                    raise ndb.Return(query_result)
