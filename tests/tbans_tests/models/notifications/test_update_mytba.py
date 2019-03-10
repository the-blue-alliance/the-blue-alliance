import unittest2

from consts.notification_type import NotificationType

from tbans.consts.platform_payload_type import PlatformPayloadType
from tbans.models.notifications.update_mytba import UpdateMyTBANotification

from tests.tbans_tests.mocks.notifications.mock_update_mytba_notification import MockUpdateMyTBANotification


class TestUpdateMyTBANotification(unittest2.TestCase):

    def test_str(self):
        notification = MockUpdateMyTBANotification('typezor', 'abcd', 'efgh')
        self.assertEquals(str(notification), 'MockUpdateMyTBANotification(data_payload={\'sending_device_key\': \'efgh\'} platform_payload=PlatformPayload(platform_type=None priority=None collapse_key="abcd_typezor_update") type_name=typezor user_id=abcd sending_device_key=efgh)')

    def test_type_name(self):
        with self.assertRaises(ValueError):
            UpdateMyTBANotification(None, 'abcd', 'efgh')

    def test_type_name_type(self):
        with self.assertRaises(TypeError):
            UpdateMyTBANotification(200, 'abcd', 'efgh')

    def test_user_id(self):
        with self.assertRaises(ValueError):
            UpdateMyTBANotification('abc', None, 'efgh')

    def test_user_id_type(self):
        with self.assertRaises(TypeError):
            UpdateMyTBANotification('abc', 200, 'efgh')

    def test_sending_device_key(self):
        with self.assertRaises(ValueError):
            UpdateMyTBANotification('abc', 'def', None)

    def test_sending_device_key_type(self):
        with self.assertRaises(TypeError):
            UpdateMyTBANotification('abc', 'def', 200)

    def test_data_payload(self):
        notification = UpdateMyTBANotification('typezor', 'abcd', 'efgh')
        self.assertEquals(notification.data_payload, {'sending_device_key': 'efgh'})

    def test_webhook_payload(self):
        notification = UpdateMyTBANotification('typezor', 'abcd', 'efgh')
        self.assertEquals(notification.webhook_payload, None)

    def test_platform_payload(self):
        notification = UpdateMyTBANotification('typezor', 'abcd', 'efgh')
        self.assertEquals(notification.platform_payload.platform_payload_dict(PlatformPayloadType.APNS), {'apns-collapse-id': 'abcd_typezor_update'})
