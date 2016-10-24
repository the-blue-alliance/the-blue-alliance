from google.appengine.ext import ndb


CACHE_DATA = {}


def get(cache_key):
    full_cache_key = '{}:{}'.format(cache_key, ndb.get_context().__hash__())
    return CACHE_DATA.get(full_cache_key, None)


def set(cache_key, value):
    full_cache_key = '{}:{}'.format(cache_key, ndb.get_context().__hash__())
    CACHE_DATA[full_cache_key] = value
