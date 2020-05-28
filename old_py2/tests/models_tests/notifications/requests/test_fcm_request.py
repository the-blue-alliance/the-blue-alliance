from firebase_admin import messaging
from mock import Mock, patch
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.fcm.platform_priority import PlatformPriority
from models.fcm.platform_config import PlatformConfig
from models.notifications.requests.request import Request
from models.notifications.requests.fcm_request import FCMRequest, MAXIMUM_TOKENS
from sitevars.notifications_enable import NotificationsEnable

from tests.mocks.notifications.mock_notification import MockNotification


class TestFCMRequest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.app = Mock()

    def tearDown(self):
        self.testbed.deactivate()

    def test_subclass(self):
        request = FCMRequest(self.app, MockNotification(), tokens=['abcd'])
        self.assertTrue(isinstance(request, Request))

    def test_init_app(self):
        FCMRequest(self.app, notification=MockNotification(), tokens=['abcd'])

    def test_init_delivery_none(self):
        with self.assertRaises(TypeError):
            FCMRequest(self.app, notification=MockNotification())

    def test_init_delivery_too_many_tokens(self):
        with self.assertRaises(ValueError) as ex:
            FCMRequest(self.app, notification=MockNotification(), tokens=['a' for i in range(MAXIMUM_TOKENS + 1)])
        self.assertEqual(str(ex.exception), 'FCMRequest tokens must contain less than {} tokens'.format(MAXIMUM_TOKENS))

    def test_str(self):
        request = FCMRequest(self.app, notification=MockNotification(), tokens=['abc'])
        self.assertEqual("FCMRequest(tokens=['abc'], notification=MockNotification())", str(request))

    def test_send(self):
        batch_response = messaging.BatchResponse([messaging.SendResponse({'name': 'abc'}, None)])
        request = FCMRequest(app=self.app, notification=MockNotification(), tokens=['abc'])
        with patch.object(messaging, 'send_multicast', return_value=batch_response) as mock_send, patch.object(request, 'defer_track_notification') as mock_track:
            response = request.send()
        mock_send.assert_called_once()
        mock_track.assert_called_once_with(1)
        self.assertEqual(response, batch_response)

    def test_send_failed(self):
        batch_response = messaging.BatchResponse([messaging.SendResponse(None, 'a')])
        request = FCMRequest(app=self.app, notification=MockNotification(), tokens=['abc', 'def'])
        with patch.object(messaging, 'send_multicast', return_value=batch_response) as mock_send, patch.object(request, 'defer_track_notification') as mock_track:
            response = request.send()
        mock_send.assert_called_once()
        mock_track.assert_not_called()
        self.assertEqual(response, batch_response)

    def test_send_failed_partial(self):
        batch_response = messaging.BatchResponse([messaging.SendResponse({'name': 'abc'}, None), messaging.SendResponse(None, 'a')])
        request = FCMRequest(app=self.app, notification=MockNotification(), tokens=['abc', 'def'])
        with patch.object(messaging, 'send_multicast', return_value=batch_response) as mock_send, patch.object(request, 'defer_track_notification') as mock_track:
            response = request.send()
        mock_send.assert_called_once()
        mock_track.assert_called_once_with(1)
        self.assertEqual(response, batch_response)

    def test_fcm_message_empty(self):
        request = FCMRequest(self.app, notification=MockNotification(), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_apns_sound(self):
        request = FCMRequest(self.app, notification=MockNotification(fcm_notification=messaging.Notification(title='Title', body='Some body message')), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertTrue(isinstance(message.notification, messaging.Notification))
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertTrue(isinstance(message.apns.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(message.apns.payload.aps, messaging.Aps))
        self.assertIsNotNone(message.apns.payload.aps.sound)
        self.assertFalse(message.apns.payload.aps.content_available)
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_apns_content_available(self):
        request = FCMRequest(self.app, notification=MockNotification(), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertTrue(isinstance(message.apns.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(message.apns.payload.aps, messaging.Aps))
        self.assertIsNone(message.apns.payload.aps.sound)
        self.assertTrue(message.apns.payload.aps.content_available)
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_platform_config(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self.app, notification=MockNotification(platform_config=platform_config), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertTrue(isinstance(message.android, messaging.AndroidConfig))
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertTrue(isinstance(message.webpush, messaging.WebpushConfig))
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_platform_config_override(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        apns_config = messaging.APNSConfig(headers={'apns-collapse-id': 'ios_collapse_key'})
        request = FCMRequest(self.app, notification=MockNotification(platform_config=platform_config, apns_config=apns_config), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertTrue(isinstance(message.android, messaging.AndroidConfig))
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertEqual(message.apns.headers, {'apns-collapse-id': 'ios_collapse_key'})
        self.assertTrue(isinstance(message.webpush, messaging.WebpushConfig))
        self.assertEqual(message.webpush.headers, {'Topic': 'collapse_key', 'Urgency': 'high'})
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_data_payload_default(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self.app, notification=MockNotification(), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertEqual(message.data, {'notification_type': 'verification'})
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_data_payload(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self.app, notification=MockNotification(data_payload={'some_data': 'some test data'}), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertEqual(message.data, {'notification_type': 'verification', 'some_data': 'some test data'})
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_data_payload_none(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self.app, notification=MockNotification(data_payload={'some_data': 'some test data', 'some_none': None}), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertEqual(message.data, {'notification_type': 'verification', 'some_data': 'some test data'})
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])

    def test_fcm_message_notification(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self.app, notification=MockNotification(fcm_notification=messaging.Notification(title='Title', body='Some body message')), tokens=['abc'])
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertTrue(isinstance(message.notification, messaging.Notification))
        self.assertIsNone(message.android)
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertIsNone(message.webpush)
        self.assertEqual(message.tokens, ['abc'])
