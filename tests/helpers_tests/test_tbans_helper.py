from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from mock import patch
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.client_type import ClientType
from helpers.tbans_helper import TBANSHelper, _firebase_app
from models.account import Account
from models.mobile_client import MobileClient


class TestTBANSHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_firebase_app(self):
        # Make sure we can get an original Firebase app
        app_one = _firebase_app()
        self.assertIsNotNone(app_one)
        self.assertEqual(app_one.name, 'tbans')
        # Make sure duplicate calls don't crash
        app_two = _firebase_app()
        self.assertIsNotNone(app_two)
        self.assertEqual(app_two.name, 'tbans')
        # Should be the same object
        self.assertEqual(app_one, app_two)

    def test_ping_client(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone')

        with patch.object(TBANSHelper, '_ping_client', return_value=True) as mock_ping_client:
            success = TBANSHelper.ping(client)
        mock_ping_client.assert_called_once_with(client)
        self.assertTrue(success)

    def test_ping_webhook(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='https://thebluealliance.com',
            client_type=ClientType.WEBHOOK,
            secret='secret',
            display_name='Webhook')

        with patch.object(TBANSHelper, '_ping_webhook', return_value=True) as mock_ping_webhook:
            success = TBANSHelper.ping(client)
        mock_ping_webhook.assert_called_once_with(client)
        self.assertTrue(success)

    def test_ping_fcm(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone')

        batch_response = messaging.BatchResponse([messaging.SendResponse({'name': 'abc'}, None)])
        from models.notifications.requests.fcm_request import FCMRequest
        with patch.object(FCMRequest, 'send', return_value=batch_response) as mock_send:
            success = TBANSHelper._ping_client(client)
        mock_send.assert_called_once()
        self.assertTrue(success)

    def test_ping_fcm_fail(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone')

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, FirebaseError(500, 'testing'))])
        from models.notifications.requests.fcm_request import FCMRequest
        with patch.object(FCMRequest, 'send', return_value=batch_response) as mock_send:
            success = TBANSHelper._ping_client(client)
        mock_send.assert_called_once()
        self.assertFalse(success)

    def test_ping_android(self):
        client_type = ClientType.OS_ANDROID
        messaging_id = 'token'

        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id=messaging_id,
            client_type=client_type,
            device_uuid='uuid',
            display_name='Phone')

        from notifications.base_notification import BaseNotification
        with patch.object(BaseNotification, 'send') as mock_send:
            success = TBANSHelper._ping_client(client)
        mock_send.assert_called_once_with({client_type: [messaging_id]})
        self.assertTrue(success)

    def test_ping_fcm_unsupported(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=-1,
            device_uuid='uuid',
            display_name='Phone')

        with self.assertRaises(Exception, msg='Unsupported FCM client type: -1'):
            TBANSHelper._ping_client(client)

    def test_ping_webhook_success(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='https://thebluealliance.com',
            client_type=ClientType.WEBHOOK,
            secret='secret',
            display_name='Webhook')

        from models.notifications.requests.webhook_request import WebhookRequest
        with patch.object(WebhookRequest, 'send', return_value=True) as mock_send:
            success = TBANSHelper._ping_webhook(client)
        mock_send.assert_called_once()
        self.assertTrue(success)

    def test_ping_webhook_failure(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='https://thebluealliance.com',
            client_type=ClientType.WEBHOOK,
            secret='secret',
            display_name='Webhook')

        from models.notifications.requests.webhook_request import WebhookRequest
        with patch.object(WebhookRequest, 'send', return_value=False) as mock_send:
            success = TBANSHelper._ping_webhook(client)
        mock_send.assert_called_once()
        self.assertFalse(success)

    def test_verification(self):
        from models.notifications.requests.webhook_request import WebhookRequest
        with patch.object(WebhookRequest, 'send') as mock_send:
            verification_key = TBANSHelper.verify_webhook('https://thebluealliance.com', 'secret')
        mock_send.assert_called_once()
        self.assertIsNotNone(verification_key)
