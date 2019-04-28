import unittest2

from consts.notification_type import NotificationType

from tbans.models.notifications.verification import VerificationNotification


class TestVerificationNotification(unittest2.TestCase):

    def test_str(self):
        notification = VerificationNotification('https://thebluealliance.com/', 'password')
        self.assertTrue("{'verification_key': " in str(notification))

    def test_url(self):
        with self.assertRaises(TypeError):
            VerificationNotification(None, 'password')

    def test_url_type(self):
        with self.assertRaises(TypeError):
            VerificationNotification(200, 'password')

    def test_url_empty(self):
        with self.assertRaises(ValueError):
            VerificationNotification('', 'password')

    def test_secret(self):
        with self.assertRaises(TypeError):
            VerificationNotification('https://thebluealliance.com/', None)

    def test_secret_type(self):
        with self.assertRaises(TypeError):
            VerificationNotification('https://thebluealliance.com/', 200)

    def test_secret_empty(self):
        with self.assertRaises(ValueError):
            VerificationNotification('https://thebluealliance.com/', '')

    def test_type(self):
        self.assertEqual(VerificationNotification._type(), NotificationType.VERIFICATION)

    def test_data_payload(self):
        notification = VerificationNotification('https://thebluealliance.com/', 'password')
        self.assertIsNone(notification.data_payload)

    def test_webhook_payload(self):
        notification = VerificationNotification('https://thebluealliance.com/', 'password')
        self.assertIsNotNone(notification.webhook_payload)
        verification_key = notification.webhook_payload.get('verification_key', None)
        self.assertIsNotNone(verification_key)
