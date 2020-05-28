import unittest2

from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from notifications.ping import PingNotification


class TestUserPingNotification(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        self.notification = PingNotification()

    def tearDown(self):
        self.testbed.deactivate()

    def test_build(self):
        expected = {}
        expected['notification_type'] = NotificationType.type_names[NotificationType.PING]
        expected['message_data'] = {'title': "Test Message",
                                    'desc': "This is a test message ensuring your device can recieve push messages from The Blue Alliance."}

        data = self.notification._build_dict()

        self.assertEqual(expected, data)
