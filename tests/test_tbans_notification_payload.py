import unittest2

from tbans.models.notifications.payloads.notification_payload import NotificationPayload


class TestNotificationPayload(unittest2.TestCase):

    def test_str(self):
        payload = NotificationPayload(title='Title Here', body='Body here')
        self.assertEqual(str(payload), 'NotificationPayload(title="Title Here" body="Body here")')

    def test_payload_title_none(self):
        with self.assertRaises(ValueError):
            NotificationPayload(title=None, body='abc')

    def test_payload_title_type(self):
        with self.assertRaises(TypeError):
            NotificationPayload(title=False, body='abc')

    def test_payload_body_none(self):
        with self.assertRaises(ValueError):
            NotificationPayload(title='abc', body=None)

    def test_payload_body_type(self):
        with self.assertRaises(TypeError):
            NotificationPayload(title='abc', body=False)

    def test_payload_dict(self):
        payload_one = NotificationPayload(title='Title Here', body='Body here')
        self.assertEqual(payload_one.payload_dict, {'title': 'Title Here', 'body': 'Body here'})
