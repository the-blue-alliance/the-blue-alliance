from google.appengine.api import memcache
from google.cloud.ndb.global_cache import GlobalCache


class ManagedMemcacheNdbCache(GlobalCache):
    """
    A caching implementation for Google Cloud NDB
    based on the python2 runtime's managed memcache

    https://cloud.google.com/appengine/docs/standard/python/memcache

    This will let us begin to migrate to the py3-compatible
    ndb library without changing functionality, initially.

    This class should be created per-request, as the CAS
    semantics are not thread-safe
    """

    KEY_PREFIX = 'cloud-ndb'

    def __init__(self):
        self.client = memcache.Client()

    def get(self, keys):
        """Retrieve entities from the cache.
        Arguments:
            keys (List[bytes]): The keys to get.
        Returns:
            List[Union[bytes, None]]]: Serialized entities, or :data:`None`,
                for each key.
        """
        cache_values = self.client.get_multi(keys, key_prefix=self.KEY_PREFIX)
        return [cache_values.get(k) for k in keys]
        
    def set(self, items, expires=None):
        """Store entities in the cache.
        Arguments:
            items (Dict[bytes, Union[bytes, None]]): Mapping of keys to
                serialized entities.
            expires (Optional[float]): Number of seconds until value expires.
        """
        self.client.set_multi(items, time=expires or 0, key_prefix=self.KEY_PREFIX)

    def delete(self, keys):
        """Remove entities from the cache.
        Arguments:
            keys (List[bytes]): The keys to remove.
        """
        self.client.delete_multi(keys, key_prefix=self.KEY_PREFIX)

    def watch(self, keys):
        """Begin an optimistic transaction for the given keys.
        A future call to :meth:`compare_and_swap` will only set values for keys
        whose values haven't changed since the call to this method.
        Arguments:
            keys (List[bytes]): The keys to watch.
        """
        self.client.get_multi(keys, key_prefix=self.KEY_PREFIX, for_cas=True)

    def compare_and_swap(self, items, expires=None):
        """Like :meth:`set` but using an optimistic transaction.
        Only keys whose values haven't changed since a preceding call to
        :meth:`watch` will be changed.
        Arguments:
            items (Dict[bytes, Union[bytes, None]]): Mapping of keys to
                serialized entities.
            expires (Optional[float]): Number of seconds until value expires.
        """
        self.client.cas_multi(items, time=expires or 0, key_prefix=self.KEY_PREFIX)
