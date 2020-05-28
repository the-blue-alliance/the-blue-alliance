from firebase_admin import messaging
import unittest2

from consts.fcm.platform_priority import PlatformPriority
from consts.fcm.platform_type import PlatformType
from models.fcm.platform_config import PlatformConfig
from models.notifications.notification import Notification

from tests.mocks.notifications.mock_notification import MockNotification


class TestNotification(unittest2.TestCase):

    def test_str(self):
        fcm_notification = messaging.Notification(title='Title Here', body='Body here')
        data_payload = {'data': 'payload'}
        platform_config = PlatformConfig(priority=PlatformPriority.HIGH, collapse_key='general_collapse_key')
        apns_config = messaging.APNSConfig(headers={'apns-collapse-id': 'ios_collapse_key'})

        notification = MockNotification(fcm_notification=fcm_notification, data_payload=data_payload, platform_config=platform_config, apns_config=apns_config)
        self.assertEqual(str(notification), 'MockNotification(data_payload={\'data\': \'payload\'} fcm_notification.title="Title Here" fcm_notification.body="Body here" platform_config=PlatformConfig(collapse_key="general_collapse_key" priority=1) apns_config={\'apns-collapse-id\': \'ios_collapse_key\'} webhook_message_data={\'data\': \'payload\'})')

    def test_type_raises(self):
        with self.assertRaises(NotImplementedError):
            Notification._type()

    def test_webhook_message_data_same_data_payload(self):
        data_payload = {'data': 'here'}
        notification = MockNotification(data_payload=data_payload)
        self.assertEqual(notification.data_payload, data_payload)
        self.assertEqual(notification.webhook_message_data, data_payload)

    def test_webhook_message_data(self):
        webhook_message_data = {'data': 'here'}
        notification = MockNotification(webhook_message_data=webhook_message_data)
        self.assertIsNone(notification.data_payload)
        self.assertEqual(notification.webhook_message_data, webhook_message_data)
