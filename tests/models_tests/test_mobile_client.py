import unittest2

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

    def test_clients(self):
        user_id_one = 'user_id_one'
        token_one = 'token1'
        token_two = 'token2'

        user_id_two = 'user_id_two'
        token_three = 'token3'

        user_id_three = 'user_id_three'

        for (user_id, tokens) in [(user_id_one, [token_one, token_two]), (user_id_two, [token_three])]:
            clients = [MobileClient(
                        parent=ndb.Key(Account, user_id),
                        user_id=user_id,
                        messaging_id=token,
                        client_type=ClientType.OS_IOS,
                        device_uuid=token[::-1],
                        display_name='Phone') for token in tokens]
            for client in clients:
                client.put()

        self.assertEqual([client.messaging_id for client in MobileClient.clients(user_id_one)], [token_one, token_two])
        self.assertEqual([client.messaging_id for client in MobileClient.clients(user_id_two)], [token_three])
        self.assertEqual([client.messaging_id for client in MobileClient.clients(user_id_three)], [])

    def test_clients_type(self):
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id_{}'.format(client_type),
                    client_type=client_type) for client_type in ClientType.names.keys()]
        for client in clients:
            client.put()

        self.assertEqual([client.messaging_id for client in MobileClient.clients('user_id', client_types=[ClientType.OS_ANDROID])], ['messaging_id_0'])
        self.assertEqual([client.messaging_id for client in MobileClient.clients('user_id', client_types=ClientType.FCM_CLIENTS)], ['messaging_id_1', 'messaging_id_3'])
        self.assertEqual([client.messaging_id for client in MobileClient.clients('user_id', client_types=[ClientType.WEBHOOK])], ['messaging_id_2'])

    def test_fcm_messaging_ids(self):
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

        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_one), [token_one, token_two])
        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_two), [token_three])
        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_three), [])

    def test_fcm_messaging_ids_unsupported_type(self):
        user_id = 'user_id'

        for (token, os) in [('a', ClientType.OS_ANDROID), ('b', ClientType.OS_IOS), ('c', ClientType.WEBHOOK), ('d', ClientType.WEB)]:
            MobileClient(
                parent=ndb.Key(Account, user_id),
                user_id=user_id,
                messaging_id=token,
                client_type=os,
                device_uuid=token,
                display_name=token).put()

        self.assertEqual(MobileClient.fcm_messaging_ids(user_id), ['b', 'd'])

    def test_delete_for_messaging_id(self):
        user_id_one = 'user_id_one'
        messaging_id_one = 'messaging_id1'
        messaging_id_two = 'messaging_id2'

        user_id_two = 'user_id_two'
        messaging_id_three = 'messaging_id3'

        for (user_id, messaging_ids) in [(user_id_one, [messaging_id_one, messaging_id_two]), (user_id_two, [messaging_id_three])]:
            for messaging_id in messaging_ids:
                MobileClient(
                    parent=ndb.Key(Account, user_id),
                    user_id=user_id,
                    messaging_id=messaging_id,
                    client_type=ClientType.OS_IOS,
                    device_uuid=messaging_id[::-1],
                    display_name='Phone').put()

        MobileClient.delete_for_messaging_id(messaging_id_one)

        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_one), [messaging_id_two])
        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_two), [messaging_id_three])

        MobileClient.delete_for_messaging_id(messaging_id_two)

        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_one), [])
        self.assertEqual(MobileClient.fcm_messaging_ids(user_id_two), [messaging_id_three])

        MobileClient.delete_for_messaging_id('does_not_exist')
