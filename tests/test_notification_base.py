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
        self.keys = {ClientType.OS_ANDROID: ["abc123"], ClientType.WEBHOOK: ["123abc"]}
        self.notification.keys = self.keys

    def tearDown(self):
        self.testbed.deactivate()

    def test_render_android(self):
        self._test_render_gcm(ClientType.OS_ANDROID)

    def test_render_webhook(self):
        message = self.notification._render_webhook()
        expect = {
            'message_type': 'ping',
            'message_data': {
                'title': 'Test Message',
                'desc': 'This is a test message ensuring your device can recieve push messages from The Blue Alliance.'
            }
        }
        self.assertEqual(message, expect)

    def _test_render_gcm(self, client_type):
        message = self.notification._render_gcm(client_type)

        self.assertEqual(self.keys[client_type], message.device_tokens)
        self.assertEqual(self.notification._build_dict(), message.notification)

    def test_render_method(self):
        self.assertEqual(self.notification.render_method(ClientType.OS_ANDROID), self.notification._render_android)
        self.assertEqual(self.notification.render_method(ClientType.WEBHOOK), self.notification._render_webhook)

    def test_render_method_renders(self):
        client_type = ClientType.OS_ANDROID
        client_render_method = self.notification.render_method(client_type)

        message = client_render_method()
        self.assertEqual(self.keys[client_type], message.device_tokens)
        self.assertEqual(self.notification._build_dict(), message.notification)
