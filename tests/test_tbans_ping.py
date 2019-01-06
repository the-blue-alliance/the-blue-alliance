import unittest2

from consts.notification_type import NotificationType

from tbans.models.notifications.ping import PingNotification


class TestPingNotification(unittest2.TestCase):

    def test_type(self):
        self.assertEqual(PingNotification._type(), NotificationType.PING)

    def test_notification_payload(self):
        notification = PingNotification()
        self.assertIsNotNone(notification.notification_payload)
        notification_payload = notification.notification_payload
        self.assertEqual(notification_payload.payload_dict, {'title': notification._title, 'body': notification._body})

    def test_data_payload(self):
        notification = PingNotification()
        self.assertIsNone(notification.data_payload)

    def test_webhook_payload(self):
        notification = PingNotification()
        self.assertEqual(notification.webhook_payload, {'title': notification._title, 'desc': notification._body})
