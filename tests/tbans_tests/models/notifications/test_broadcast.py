import unittest2

from tba.consts.notification_type import NotificationType

from tbans.models.notifications.broadcast import BroadcastNotification


class TestBroadcastNotification(unittest2.TestCase):

    def setUp(self):
        self.notification = BroadcastNotification('Title Here', 'Some body message ya dig', 'https://thebluealliance.com/')

    def test_type(self):
        self.assertEqual(BroadcastNotification._type(), NotificationType.BROADCAST)

    def test_fcm_notification(self):
        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'Title Here')
        self.assertEqual(self.notification.fcm_notification.body, 'Some body message ya dig')

    def test_data_payload(self):
        self.assertEqual(self.notification.data_payload, {'url': 'https://thebluealliance.com/', 'app_version': None})

    def test_data_payload_app_version(self):
        notification = BroadcastNotification('T', 'B', 'https://thebluealliance.com/', '1.0.0')
        self.assertEqual(notification.data_payload, {'url': 'https://thebluealliance.com/', 'app_version': '1.0.0'})

    def test_webhook_message_data(self):
        payload = {'title': 'Title Here', 'desc': 'Some body message ya dig', 'url': 'https://thebluealliance.com/', 'app_version': None}
        self.assertEqual(self.notification.webhook_message_data, payload)

    def test_webhook_message_data_app_version(self):
        notification = BroadcastNotification('T', 'B', 'https://thebluealliance.com/', '1.0.0')
        payload = {'title': 'T', 'desc': 'B', 'url': 'https://thebluealliance.com/', 'app_version': '1.0.0'}
        self.assertEqual(notification.webhook_message_data, payload)
