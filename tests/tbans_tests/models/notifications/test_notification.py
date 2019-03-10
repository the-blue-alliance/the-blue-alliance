import unittest2

from tbans.consts.platform_payload_priority import PlatformPayloadPriority
from tbans.consts.platform_payload_type import PlatformPayloadType

from tbans.models.notifications.notification import Notification
from tbans.models.notifications.payloads.notification_payload import NotificationPayload
from tbans.models.notifications.payloads.platform_payload import PlatformPayload

from tests.tbans_tests.mocks.notifications.mock_notification import MockNotification


class TestNotification(unittest2.TestCase):

    def test_str(self):
        notification_payload = NotificationPayload(title='Title Here', body='Body here')
        data_payload = {'data': 'payload'}
        platform_payload = PlatformPayload(priority=PlatformPayloadPriority.HIGH, collapse_key='general_collapse_key')
        apns_payload = PlatformPayload(platform_type=PlatformPayloadType.APNS, priority=PlatformPayloadPriority.NORMAL, collapse_key='ios_collapse_key')

        notification = MockNotification(notification_payload=notification_payload, data_payload=data_payload, platform_payload=platform_payload, apns_payload=apns_payload)
        self.assertEqual(str(notification), 'MockNotification(data_payload={\'data\': \'payload\'} notification_payload=NotificationPayload(title="Title Here" body="Body here") platform_payload=PlatformPayload(platform_type=None priority=1 collapse_key="general_collapse_key") apns_payload=PlatformPayload(platform_type=1 priority=0 collapse_key="ios_collapse_key") webhook_payload={\'data\': \'payload\'})')

    def test_type_raises(self):
        with self.assertRaises(NotImplementedError):
            Notification._type()

    def test_webhook_payload_same_data_payload(self):
        data_payload = {'data': 'here'}
        notification = MockNotification(data_payload=data_payload)
        self.assertEqual(notification.data_payload, data_payload)
        self.assertEqual(notification.webhook_payload, data_payload)

    def test_webhook_payload(self):
        webhook_payload = {'data': 'here'}
        notification = MockNotification(webhook_payload=webhook_payload)
        self.assertIsNone(notification.data_payload)
        self.assertEqual(notification.webhook_payload, webhook_payload)
