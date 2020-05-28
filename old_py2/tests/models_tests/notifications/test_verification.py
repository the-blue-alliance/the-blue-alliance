import unittest2

from consts.notification_type import NotificationType

from models.notifications.verification import VerificationNotification


class TestVerificationNotification(unittest2.TestCase):

    def test_str(self):
        notification = VerificationNotification('https://thebluealliance.com/', 'password')
        self.assertTrue("{'verification_key': " in str(notification))

    def test_type(self):
        self.assertEqual(VerificationNotification._type(), NotificationType.VERIFICATION)

    def test_data_payload(self):
        notification = VerificationNotification('https://thebluealliance.com/', 'password')
        self.assertIsNone(notification.data_payload)

    def test_webhook_message_data(self):
        notification = VerificationNotification('https://thebluealliance.com/', 'password')
        self.assertIsNotNone(notification.webhook_message_data)
        verification_key = notification.webhook_message_data.get('verification_key', None)
        self.assertIsNotNone(verification_key)
