import unittest2

from tbans.models.requests.notifications.notification_request import NotificationRequest

from tests.tbans_tests.mocks.notifications.mock_notification import MockNotification


class TestNotificationRequest(unittest2.TestCase):

    def test_init_notification_none(self):
        with self.assertRaises(TypeError):
            NotificationRequest(notification=None)

    def test_init_notification_value(self):
        with self.assertRaises(TypeError):
            NotificationRequest(notification='abcd')

    def test_json_string(self):
        request = NotificationRequest(notification=MockNotification())
        with self.assertRaises(NotImplementedError):
            request.json_string()

    def test_json_string(self):
        request = NotificationRequest(notification=MockNotification())
        with self.assertRaises(NotImplementedError):
            request.send()
