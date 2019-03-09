import unittest2

from tbans.models.messages.message import Message

from tests.tbans.mocks.notifications.mock_notification import MockNotification


class TestMessage(unittest2.TestCase):

    def test_init_notification_none(self):
        with self.assertRaises(ValueError):
            Message(notification=None)

    def test_init_notification_value(self):
        with self.assertRaises(TypeError):
            Message(notification='abcd')

    def test_json_string(self):
        message = Message(notification=MockNotification())
        with self.assertRaises(NotImplementedError):
            message.json_string()

    def test_json_string(self):
        message = Message(notification=MockNotification())
        with self.assertRaises(NotImplementedError):
            message.send()
