import unittest2
import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.account import Account
from models.subscription import Subscription


class TestMobileClient(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_user_subscriptions(self):
        user_id_one = 'user_id_one'
        user_id_two = 'user_id_two'

        for key in ['abc', 'def']:
            Subscription(
                parent=ndb.Key(Account, user_id_one),
                user_id=user_id_one,
                model_type=1,
                model_key=key,
                notification_types=[]
            ).put()

        self.assertEqual(len(Subscription.user_subscriptions(user_id_one)), 2)
        self.assertEqual(len(Subscription.user_subscriptions(user_id_two)), 0)
