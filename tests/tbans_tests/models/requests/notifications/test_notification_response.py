import unittest2

from tbans.models.requests.notifications.notification_response import NotificationResponse


class TestNotificationResponse(unittest2.TestCase):

    def test_status_code(self):
        with self.assertRaises(ValueError):
            NotificationResponse(status_code=None)

    def test_status_code_type(self):
        with self.assertRaises(TypeError):
            NotificationResponse(status_code='abc')

    def test_content_type(self):
        with self.assertRaises(TypeError):
            NotificationResponse(status_code=200, content=200)

    def test_init(self):
        _status_code = 404
        _content = 'Some content here'
        response = NotificationResponse(status_code=_status_code, content=_content)
        self.assertEqual(response.status_code, _status_code)
        self.assertEqual(response.content, _content)

    def test_str(self):
        response = NotificationResponse(status_code=400)
        self.assertEqual(str(response), 'NotificationResponse(code=400 content=None)')

    def test_str_content(self):
        response = NotificationResponse(status_code=400, content='Some content here')
        self.assertEqual(str(response), 'NotificationResponse(code=400 content="Some content here")')
