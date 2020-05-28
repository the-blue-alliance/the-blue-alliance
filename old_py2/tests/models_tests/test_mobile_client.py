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

    def test_clients_empty(self):
        abc = MobileClient(
            parent=ndb.Key(Account, 'abc'),
            user_id='abc',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone'
        )
        abc.put()
        unverified = MobileClient(
            parent=ndb.Key(Account, 'efg'),
            user_id='efg',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone',
            verified=False
        )
        unverified.put()
        # Test empty users returns empty
        self.assertEqual(MobileClient.clients(users=[]), [])
        # Test empty client types return empty
        self.assertEqual(MobileClient.clients(users=['abc'], client_types=[]), [])
        # Test empty users and client types returns empty
        self.assertEqual(MobileClient.clients(users=[], client_types=[]), [])
        # Test client type + users does not return empty
        self.assertEqual(MobileClient.clients(users=['abc']), [abc])
        # Test fetching for only verified
        self.assertEqual(MobileClient.clients(users=['efg']), [])

    def test_clients_multiple(self):
        abc = MobileClient(
            parent=ndb.Key(Account, 'abc'),
            user_id='abc',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone'
        )
        abc.put()
        efg = MobileClient(
            parent=ndb.Key(Account, 'efg'),
            user_id='efg',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone'
        )
        efg.put()
        self.assertEqual(MobileClient.clients(['abc', 'efg']), [abc, efg])

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

        self.assertEqual([client.messaging_id for client in MobileClient.clients([user_id_one])], [token_one, token_two])
        self.assertEqual([client.messaging_id for client in MobileClient.clients([user_id_two])], [token_three])
        self.assertEqual([client.messaging_id for client in MobileClient.clients([user_id_one, user_id_two])], [token_one, token_two, token_three])
        self.assertEqual([client.messaging_id for client in MobileClient.clients([user_id_three])], [])

    def test_clients_type(self):
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id_{}'.format(client_type),
                    client_type=client_type) for client_type in ClientType.names.keys()]
        for client in clients:
            client.put()

        self.assertEqual([client.messaging_id for client in MobileClient.clients(['user_id'], client_types=[ClientType.OS_ANDROID])], ['messaging_id_0'])
        self.assertEqual([client.messaging_id for client in MobileClient.clients(['user_id'], client_types=ClientType.FCM_CLIENTS)], ['messaging_id_1', 'messaging_id_3'])
        self.assertEqual([client.messaging_id for client in MobileClient.clients(['user_id'], client_types=[ClientType.WEBHOOK])], ['messaging_id_2'])

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

        clients_one = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_one').fetch()]
        clients_two = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_two').fetch()]

        self.assertEqual(clients_one, [messaging_id_two])
        self.assertEqual(clients_two, [messaging_id_three])

        MobileClient.delete_for_messaging_id(messaging_id_two)

        clients_one = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_one').fetch()]
        clients_two = [client.messaging_id for client in MobileClient.query(MobileClient.user_id == 'user_id_two').fetch()]

        self.assertEqual(clients_one, [])
        self.assertEqual(clients_two, [messaging_id_three])

        MobileClient.delete_for_messaging_id('does_not_exist')
