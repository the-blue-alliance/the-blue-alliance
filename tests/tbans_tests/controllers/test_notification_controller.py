from firebase_admin import messaging
import unittest2
import webapp2
import webtest

from tba.consts.client_type import ClientType
from tba.consts.notification_type import NotificationType
from tba.models.mobile_client import MobileClient

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.account import Account

from tbans.controllers.notification_controller import NotificationHandler
from tbans.models.notifications.update_favorites import UpdateFavoritesNotification
from tbans.models.notifications.update_subscriptions import UpdateSubscriptionsNotification

from tests.tbans_tests.mocks.notifications.mock_notification import MockNotification


class TestNotificationHandler(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        # Stub the FCM admin module
        messaging._get_messaging_service(NotificationHandler._firebase_app()).send_all = self._stub_send_all
        # Set self._mock_batch_response to setup a response for send_all to return

        app = webapp2.WSGIApplication([
            ('/notify', NotificationHandler),
        ])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()
        self._mock_batch_response = None

    def _stub_send_all(self, message, dry_run):
        self.assertFalse(dry_run)
        self.assertIsNotNone(message)
        return self._mock_batch_response

    def test_notify_user_fcm(self):
        self.testapp.post('/notify', {'user_id': 'user_id', 'notification_type': str(NotificationType.UPDATE_FAVORITES), 'vertical_type': 0})

    def test_notify_user_webhook(self):
        self.testapp.post('/notify', {'user_id': 'user_id', 'notification_type': str(NotificationType.UPDATE_FAVORITES), 'vertical_type': 1})

    def test_send_fcm_success(self):
        self._mock_batch_response = MockBatchResponse([MockResponse()])

        mobile_client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone').put()
        success = NotificationHandler._send_fcm(MockNotification(), ['token'])

        self.assertTrue(success)
        # Make sure we didn't delete our token
        self.assertEqual(MobileClient.device_push_tokens('user_id'), ['token'])

    def test_send_fcm_delete(self):
        for code in ['mismatched-credential', 'registration-token-not-registered']:
            self._mock_batch_response = MockBatchResponse([MockResponse(exception=MockApiCallError(code, '', ''))])

            mobile_client = MobileClient(
                parent=ndb.Key(Account, 'user_id'),
                user_id='user_id',
                messaging_id='token',
                client_type=ClientType.OS_IOS,
                device_uuid='uuid',
                display_name='Phone').put()
            success = NotificationHandler._send_fcm(MockNotification(), ['token'])

            self.assertTrue(success)
            # Make sure we deleted our token
            self.assertEqual(MobileClient.device_push_tokens('user_id'), [])

    def test_send_fcm_error(self):
        self._mock_batch_response = MockBatchResponse([MockResponse(exception=MockApiCallError('invalid-argument', '', ''))])

        mobile_client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone').put()
        success = NotificationHandler._send_fcm(MockNotification(), ['token'])

        self.assertFalse(success)
        # Make sure we didn't delete our token
        self.assertEqual(MobileClient.device_push_tokens('user_id'), ['token'])

    def test_firebase_app(self):
        self.assertIsNotNone(NotificationHandler._firebase_app())

    def test_user_notification_favorites(self):
        notification = NotificationHandler._user_notification('abcd', 100)
        self.assertTrue(isinstance(notification, UpdateFavoritesNotification))
        self.assertEqual(notification.user_id, 'abcd')

    def test_user_notification_subscriptions(self):
        notification = NotificationHandler._user_notification('abcd', 101)
        self.assertTrue(isinstance(notification, UpdateSubscriptionsNotification))
        self.assertEqual(notification.user_id, 'abcd')


class MockBatchResponse:

    def __init__(self, responses):
        self.responses = responses

    @property
    def success_count(self):
        return len([response for response in self.responses if response.success])

    @property
    def failure_count(self):
        return len(self.responses) - self.success_count


class MockResponse:

    def __init__(self, exception=None):
        self.exception = exception

    @property
    def success(self):
        return self.exception == None


class MockApiCallError:

    def __init__(self, code, message, detail):
        self.code = code
        self.message = message
        self.detail = detail
