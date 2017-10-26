import unittest2

from google.appengine.ext import testbed

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from notifications.ping import PingNotification


class TestBaseNotification(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # User a Ping notification to test the render and send classes
        # It's as simple as it gets
        self.notification = PingNotification()
        self.keys = {
            ClientType.OS_ANDROID: ["abc123"],
            ClientType.WEBHOOK: ["123abc"]
        }
        self.notification.keys = self.keys

    def tearDown(self):
        self.testbed.deactivate()

    def test_render_android(self):
        message = self.notification._render_android()

        self.assertEqual(self.keys[ClientType.OS_ANDROID],
                         message.device_tokens)
        self.assertEqual(self.notification._build_dict(), message.notification)

    def test_render_webhook(self):
        message = self.notification._render_webhook()

        self.assertEqual(message, self.notification._build_dict())

    def test_render_ios(self):
        pass
