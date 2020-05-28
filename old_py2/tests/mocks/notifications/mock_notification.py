from consts.notification_type import NotificationType

from models.notifications.notification import Notification


class MockNotification(Notification):

    def __init__(self, fcm_notification=None, data_payload=None, platform_config=None, apns_config=None, webhook_message_data=None):
        super(MockNotification, self).__init__()
        self._fcm_notification = fcm_notification
        self._data_payload = data_payload
        self._platform_config = platform_config
        self._apns_config = apns_config
        self._webhook_message_data = webhook_message_data

    @staticmethod
    def _type():
        return NotificationType.VERIFICATION

    @property
    def fcm_notification(self):
        return self._fcm_notification

    @property
    def data_payload(self):
        return self._data_payload

    @property
    def platform_config(self):
        return self._platform_config

    @property
    def apns_config(self):
        return self._apns_config

    @property
    def webhook_message_data(self):
        return self._webhook_message_data if self._webhook_message_data\
            else super(MockNotification, self).webhook_message_data
