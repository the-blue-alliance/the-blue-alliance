from consts.notification_type import NotificationType

from tbans.models.notifications.notification import Notification


class MockNotification(Notification):

    def __init__(self, notification_payload=None, data_payload=None, webhook_payload=None, platform_payload=None, apns_payload=None):
        super(Notification, self).__init__()
        self._notification_payload = notification_payload
        self._data_payload = data_payload
        self._webhook_payload = webhook_payload
        self._platform_payload = platform_payload
        self._apns_payload = apns_payload

    @staticmethod
    def _type():
        return NotificationType.VERIFICATION

    @property
    def notification_payload(self):
        return self._notification_payload

    @property
    def data_payload(self):
        return self._data_payload

    @property
    def platform_payload(self):
        return self._platform_payload

    @property
    def apns_payload(self):
        return self._apns_payload

    @property
    def webhook_payload(self):
        return self._webhook_payload if self._webhook_payload else super(MockNotification, self).webhook_payload
