import unittest2

from consts.notification_type import NotificationType

from models.notifications.broadcast import BroadcastNotification


class TestBroadcastNotification(unittest2.TestCase):

    def setUp(self):
        self.notification = BroadcastNotification('Title Here', 'Some body message ya dig')

    def test_type(self):
        self.assertEqual(BroadcastNotification._type(), NotificationType.BROADCAST)

    def test_fcm_notification(self):
        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'Title Here')
        self.assertEqual(self.notification.fcm_notification.body, 'Some body message ya dig')

    def test_data_payload(self):
        self.assertEqual(self.notification.data_payload, {})

    def test_data_payload_url(self):
        notification = BroadcastNotification('T', 'B', 'https://thebluealliance.com/')
        self.assertEqual(notification.data_payload, {'url': 'https://thebluealliance.com/'})

    def test_data_payload_app_version(self):
        notification = BroadcastNotification('T', 'B', 'https://thebluealliance.com/', '1.0.0')
        self.assertEqual(notification.data_payload, {'url': 'https://thebluealliance.com/', 'app_version': '1.0.0'})

    def test_data_payload_url_app_version(self):
        notification = BroadcastNotification('T', 'B', None, '1.0.0')
        self.assertEqual(notification.data_payload, {'app_version': '1.0.0'})

    def test_webhook_message_data(self):
        payload = {'title': 'Title Here', 'desc': 'Some body message ya dig'}
        self.assertEqual(self.notification.webhook_message_data, payload)

    def test_webhook_message_data_url(self):
        notification = BroadcastNotification('T', 'B', 'https://thebluealliance.com/', None)
        payload = {'title': 'T', 'desc': 'B', 'url': 'https://thebluealliance.com/'}
        self.assertEqual(notification.webhook_message_data, payload)

    def test_webhook_message_data_app_version(self):
        notification = BroadcastNotification('T', 'B', None, '1.0.0')
        payload = {'title': 'T', 'desc': 'B'}
        self.assertEqual(notification.webhook_message_data, payload)

    def test_webhook_message_data_url_app_version(self):
        notification = BroadcastNotification('T', 'B', 'https://thebluealliance.com/', '1.0.0')
        payload = {'title': 'T', 'desc': 'B', 'url': 'https://thebluealliance.com/'}
        self.assertEqual(notification.webhook_message_data, payload)
