import unittest2

from tbans.requests.request import Request

from tests.tbans_tests.mocks.notifications.mock_notification import MockNotification


class TestRequest(unittest2.TestCase):

    def test_notification_type(self):
        with self.assertRaises(TypeError):
            request = Request('1')

    def test_notification(self):
        Request(MockNotification())

    def test_send(self):
        request = Request(MockNotification())
        with self.assertRaises(NotImplementedError):
            request.send()
