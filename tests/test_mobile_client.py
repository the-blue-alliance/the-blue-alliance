import unittest2
import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.client_type import ClientType
from models.account import Account
from models.mobile_client import MobileClient


class TestMobileClient(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_device_push_tokens(self):
        user_id_one = 'user_id_one'
        token_one = 'token1'
        token_two = 'token2'

        user_id_two = 'user_id_two'
        token_three = 'token3'

        user_id_three = 'user_id_three'

        for (user_id, tokens) in [(user_id_one, [token_one, token_two]), (user_id_two, [token_three])]:
            for token in tokens:
                MobileClient(
                    parent=ndb.Key(Account, user_id),
                    user_id=user_id,
                    messaging_id=token,
                    client_type=ClientType.OS_IOS,
                    device_uuid=token[::-1],
                    display_name='Phone').put()

        self.assertEqual(MobileClient.device_push_tokens(user_id_one), [token_one, token_two])
        self.assertEqual(MobileClient.device_push_tokens(user_id_two), [token_three])
        self.assertEqual(MobileClient.device_push_tokens(user_id_three), [])

    def test_device_push_tokens_unsupported_type(self):
        user_id = 'user_id'

        for (token, os) in [('a', ClientType.OS_ANDROID), ('b', ClientType.OS_IOS), ('c', ClientType.WEBHOOK)]:
            MobileClient(
                parent=ndb.Key(Account, user_id),
                user_id=user_id,
                messaging_id=token,
                client_type=os,
                device_uuid=token,
                display_name=token).put()

        self.assertEqual(MobileClient.device_push_tokens(user_id), ['b'])

    def test_delete_for_token(self):
        user_id_one = 'user_id_one'
        token_one = 'token1'
        token_two = 'token2'

        user_id_two = 'user_id_two'
        token_three = 'token3'

        for (user_id, tokens) in [(user_id_one, [token_one, token_two]), (user_id_two, [token_three])]:
            for token in tokens:
                MobileClient(
                    parent=ndb.Key(Account, user_id),
                    user_id=user_id,
                    messaging_id=token,
                    client_type=ClientType.OS_IOS,
                    device_uuid=token[::-1],
                    display_name='Phone').put()

        MobileClient.delete_for_token(token_one)

        self.assertEqual(MobileClient.device_push_tokens(user_id_one), [token_two])
        self.assertEqual(MobileClient.device_push_tokens(user_id_two), [token_three])

        MobileClient.delete_for_token(token_two)

        self.assertEqual(MobileClient.device_push_tokens(user_id_one), [])
        self.assertEqual(MobileClient.device_push_tokens(user_id_two), [token_three])
