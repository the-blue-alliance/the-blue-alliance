import unittest2

from google.appengine.ext import testbed

from tbans.utils.auth_utils import get_firebase_messaging_access_token


class TestAuthUtils(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_get_access_token(self):
        self.assertIsNotNone(get_firebase_messaging_access_token())
