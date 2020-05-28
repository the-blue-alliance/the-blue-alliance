import unittest2

from consts.notification_type import NotificationType

from models.notifications.ping import PingNotification


class TestPingNotification(unittest2.TestCase):

    def test_type(self):
        self.assertEqual(PingNotification._type(), NotificationType.PING)

    def test_notification_payload(self):
        notification = PingNotification()
        self.assertIsNotNone(notification.fcm_notification)
        fcm_notification = notification.fcm_notification
        self.assertEqual(fcm_notification.title,notification._title)
        self.assertEqual(fcm_notification.body, notification._body)

    def test_data_payload(self):
        notification = PingNotification()
        self.assertIsNone(notification.data_payload)

    def test_webhook_message_data(self):
        notification = PingNotification()
        self.assertEqual(notification.webhook_message_data, {'title': notification._title, 'desc': notification._body})
