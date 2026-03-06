import pickle
import zlib
from typing import Any, AnyStr, Dict, List, Optional

from flask_caching.backends.base import BaseCache
from google.appengine.api import memcache


class MemcacheFlaskResponseCache(BaseCache):
    memcache_client: memcache.Client

    def __init__(self, memcache_client: memcache.Client) -> None:
        self.memcache_client = memcache_client

    def dump_object(self, value: Any) -> bytes:
        """Dumps an object into a string for redis.  By default it serializes
        integers as regular string and pickle dumps everything else.
        """
        t = type(value)
        if t == int:
            return str(value).encode("ascii")
        return b"!" + zlib.compress(pickle.dumps(value))

    def load_object(self, value: bytes) -> Any:
        """The reversal of :meth:`dump_object`.  This might be called with
        None.
        """
        if value is None:
            return None
        if value.startswith(b"!"):
            try:
                return pickle.loads(zlib.decompress(value[1:]))
            except pickle.PickleError:
                return None
        try:
            return int(value)
        except ValueError:
            return value

    def get(self, key: AnyStr) -> Optional[Any]:
        """Look up key in the cache and return the value for it.

        :param key: the key to be looked up.
        :returns: The value if it exists and is readable, else ``None``.
        """
        return self.load_object(self.memcache_client.get(key))

    def delete(self, key: AnyStr) -> bool:
        """Delete `key` from the cache.

        :param key: the key to delete.
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """
        return self.memcache_client.delete(key)

    def get_many(self, *keys: AnyStr) -> List[Optional[Any]]:
        """Returns a list of values for the given keys.
        For each key an item in the list is created::

            foo, bar = cache.get_many("foo", "bar")

        Has the same error handling as :meth:`get`.

        :param keys: The function accepts multiple keys as positional
                     arguments.
        """
        resp = self.memcache_client.get_multi(keys)
        return [self.load_object(resp.get(k)) for k in keys]

    def get_dict(self, *keys: AnyStr) -> Dict[AnyStr, Optional[Any]]:
        """Like :meth:`get_many` but return a dict::

            d = cache.get_dict("foo", "bar")
            foo = d["foo"]
            bar = d["bar"]

        :param keys: The function accepts multiple keys as positional
                     arguments.
        """
        resp = self.memcache_client.get_multi(keys)
        return {k: self.load_object(v) for k, v in resp.items()}

    def set(self, key: AnyStr, value: Any, timeout: Optional[int] = None) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).

        :param key: the key to set
        :param value: the value for the key
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """
        return self.memcache_client.set(key, self.dump_object(value), timeout or 0)

    def add(self, key: AnyStr, value: Any, timeout: Optional[int] = None):
        """Works like :meth:`set` but does not overwrite the values of already
        existing keys.

        :param key: the key to set
        :param value: the value for the key
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 idicates that the cache never expires.
        :returns: Same as :meth:`set`, but also ``False`` for already
                  existing keys.
        :rtype: boolean
        """
        return self.memcache_client.add(key, self.dump_object(value), timeout or 0)

    def set_many(
        self, mapping: Dict[AnyStr, Any], timeout: Optional[int] = None
    ) -> bool:
        """Sets multiple keys and values from a mapping.

        :param mapping: a mapping with the keys/values to set.
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 idicates that the cache never expires.
        :returns: Whether all given keys have been set.
        :rtype: boolean
        """
        keys_not_set = self.memcache_client.set_multi(
            {k: self.dump_object(v) for k, v in mapping.items()}, timeout or 0
        )
        return len(keys_not_set) == 0

    def delete_many(self, *keys: AnyStr) -> bool:
        """Deletes multiple keys at once.

        :param keys: The function accepts multiple keys as positional
                     arguments.
        :returns: Whether all given keys have been deleted.
        :rtype: boolean
        """
        return self.memcache_client.delete_multi(keys)

    def has(self, key):
        """Checks if a key exists in the cache without returning it. This is a
        cheap operation that bypasses loading the actual data on the backend.

        This method is optional and may not be implemented on all caches.

        :param key: the key to check
        """
        raise NotImplementedError(
            "%s doesn't have an efficient implementation of `has`. That "
            "means it is impossible to check whether a key exists without "
            "fully loading the key's data. Consider using `self.get` "
            "explicitly if you don't care about performance."
        )

    def clear(self):
        """Clears the cache.  Keep in mind that not all caches support
        completely clearing the cache.

        :returns: Whether the cache has been cleared.
        :rtype: boolean
        """
        return self.memcache_client.flush_all()

    def inc(self, key: AnyStr, delta: int = 1) -> Optional[int]:
        """Increments the value of a key by `delta`.  If the key does
        not yet exist it is initialized with `delta`.

        For supporting caches this is an atomic operation.

        :param key: the key to increment.
        :param delta: the delta to add.
        :returns: The new value or ``None`` for backend errors.
        """
        return self.memcache_client.incr(key, delta)

    def dec(self, key: AnyStr, delta: int = 1):
        """Decrements the value of a key by `delta`.  If the key does
        not yet exist it is initialized with `-delta`.

        For supporting caches this is an atomic operation.

        :param key: the key to increment.
        :param delta: the delta to subtract.
        :returns: The new value or `None` for backend errors.
        """
        return self.memcache_client.decr(key, delta)
