import time
import unittest2

from services.ndb.gae_memcache_cache import ManagedMemcacheNdbCache
from google.appengine.api.memcache import memcache_stub
from google.appengine.ext import testbed


class TestManagedMemcacheNdbCache(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        self.fake_time = 0.0
        self.memcache_stub = memcache_stub.MemcacheServiceStub(gettime=self.fakeTime)
        self.testbed._register_stub(testbed.MEMCACHE_SERVICE_NAME, self.memcache_stub)

        self.cache = ManagedMemcacheNdbCache()

    def tearDown(self):
        self.testbed.deactivate()

    def fakeTime(self):
        return self.fake_time

    def test_set_get_delete(self):
        result = self.cache.set({b"one": b"foo", b"two": b"bar", b"three": b"baz"})
        self.assertIsNone(result)

        result = self.cache.get([b"two", b"three", b"one"])
        self.assertEqual(result, [b"bar", b"baz", b"foo"])

        result = self.cache.delete([b"one", b"two", b"three"])
        self.assertIsNone(result)

        result = self.cache.get([b"two", b"three", b"one"])
        self.assertEqual(result, [None, None, None])

    def test_set_get_delete_w_expires(self):
        self.fake_time = 0.0
        result = self.cache.set(
            {b"one": b"foo", b"two": b"bar", b"three": b"baz"}, expires=5
        )
        self.assertIsNone(result)

        result = self.cache.get([b"two", b"three", b"one"])
        self.assertEqual(result, [b"bar", b"baz", b"foo"])

        self.fake_time = 10.0
        result = self.cache.get([b"two", b"three", b"one"])
        self.assertEqual(result, [None, None, None])
