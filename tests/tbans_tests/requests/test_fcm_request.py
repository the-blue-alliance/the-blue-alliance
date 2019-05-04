import firebase_admin
from firebase_admin import messaging
import unittest2

from google.appengine.ext import testbed

from tbans.consts.fcm.platform_priority import PlatformPriority
from tbans.models.fcm.platform_config import PlatformConfig
from tbans.requests.request import Request
from tbans.requests.fcm_request import FCMRequest

from tests.tbans_tests.mocks.notifications.mock_notification import MockNotification


class TestFCMRequest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()
        self.testbed.setup_env(app_id='your-app-id', overwrite=True)
        # Stub the FCM admin module
        try:
            self._app = firebase_admin.get_app('tbans')
        except ValueError:
            self._app = firebase_admin.initialize_app(name='tbans')
        messaging._get_messaging_service(self._app).send = self._stub_send

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_send(self, message, dry_run):
        self.assertFalse(dry_run)
        self.assertIsNotNone(message)
        return 'message-id'

    def test_subclass(self):
        request = FCMRequest(self._app, MockNotification(), token='abcd')
        self.assertTrue(isinstance(request, Request))

    def test_init_app_none(self):
        with self.assertRaises(ValueError):
            FCMRequest(None, MockNotification(), token='abcd')

    def test_init_app_type(self):
        with self.assertRaises(ValueError):
            FCMRequest('abc', MockNotification(), token='abcd')

    def test_init_app(self):
        FCMRequest(self._app, MockNotification(), token='abcd')

    def test_init_delivery_none(self):
        with self.assertRaises(TypeError):
            FCMRequest(self._app, notification=MockNotification())

    def test_init_delivery_multiple(self):
        with self.assertRaises(TypeError):
            FCMRequest(self._app, notification=MockNotification(), token='abc', topic='def')

    def test_str_token(self):
        request = FCMRequest(self._app, MockNotification(), token='abc')
        self.assertTrue('FCMRequest(token="abc", notification=' in str(request))

    def test_str_topic(self):
        request = FCMRequest(self._app, MockNotification(), topic='def')
        self.assertTrue('FCMRequest(topic="def", notification=' in str(request))

    def test_str_condition(self):
        request = FCMRequest(self._app, MockNotification(), condition='hij')
        self.assertTrue('FCMRequest(condition="hij", notification=' in str(request))

    def test_send(self):
        request = FCMRequest(self._app, notification=MockNotification(), token='abc')
        message_id = request.send()
        self.assertEqual(message_id, 'message-id')

    def test_fcm_message_empty(self):
        request = FCMRequest(self._app, notification=MockNotification(), token='abc')
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertIsNone(message.apns)
        self.assertIsNone(message.webpush)
        self.assertEqual(message.token, 'abc')
        self.assertIsNone(message.topic)
        self.assertIsNone(message.condition)

    def test_fcm_message_platform_config(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self._app, notification=MockNotification(platform_config=platform_config), topic='abc')
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertTrue(isinstance(message.android, messaging.AndroidConfig))
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertTrue(isinstance(message.webpush, messaging.WebpushConfig))
        self.assertIsNone(message.token)
        self.assertEqual(message.topic, 'abc')
        self.assertIsNone(message.condition)

    def test_fcm_message_platform_config_override(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        apns_config = messaging.APNSConfig(headers={'apns-collapse-id': 'ios_collapse_key'})
        request = FCMRequest(self._app, notification=MockNotification(platform_config=platform_config, apns_config=apns_config), topic='abc')
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertIsNone(message.notification)
        self.assertTrue(isinstance(message.android, messaging.AndroidConfig))
        self.assertTrue(isinstance(message.apns, messaging.APNSConfig))
        self.assertEqual(message.apns.headers, {'apns-collapse-id': 'ios_collapse_key'})
        self.assertTrue(isinstance(message.webpush, messaging.WebpushConfig))
        self.assertEqual(message.webpush.headers, {'Topic': 'collapse_key', 'Urgency': 'high'})
        self.assertIsNone(message.token)
        self.assertEqual(message.topic, 'abc')
        self.assertIsNone(message.condition)

    def test_fcm_message_data_payload_default(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self._app, notification=MockNotification(), condition='abc')
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertEqual(message.data, {'notification_type': 'verification'})
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertIsNone(message.apns)
        self.assertIsNone(message.webpush)
        self.assertIsNone(message.token)
        self.assertIsNone(message.topic)
        self.assertEqual(message.condition, 'abc')

    def test_fcm_message_data_payload(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self._app, notification=MockNotification(data_payload={'some_data': 'some test data'}), condition='abc')
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertEqual(message.data, {'notification_type': 'verification', 'some_data': 'some test data'})
        self.assertIsNone(message.notification)
        self.assertIsNone(message.android)
        self.assertIsNone(message.apns)
        self.assertIsNone(message.webpush)
        self.assertIsNone(message.token)
        self.assertIsNone(message.topic)
        self.assertEqual(message.condition, 'abc')

    def test_fcm_message_notification(self):
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='collapse_key')
        request = FCMRequest(self._app, notification=MockNotification(fcm_notification=messaging.Notification(title='Title', body='Some body message')), condition='abc')
        message = request._fcm_message()
        self.assertIsNotNone(message)
        self.assertIsNotNone(message.data)
        self.assertTrue(isinstance(message.notification, messaging.Notification))
        self.assertIsNone(message.android)
        self.assertIsNone(message.apns)
        self.assertIsNone(message.webpush)
        self.assertIsNone(message.token)
        self.assertIsNone(message.topic)
        self.assertEqual(message.condition, 'abc')
