from models.notifications.notification import Notification


class BroadcastNotification(Notification):

    def __init__(self, title, message, url=None, app_version=None):
        self.title = title
        self.message = message
        self.url = url
        self.app_version = app_version

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.BROADCAST

    @property
    def fcm_notification(self):
        from firebase_admin import messaging
        return messaging.Notification(title=self.title, body=self.message)

    @property
    def data_payload(self):
        payload = {}
        if self.url:
            payload['url'] = self.url
        else:
            payload['url'] = None

        if self.app_version:
            payload['app_version'] = self.app_version
        else:
            payload['app_version'] = None

        return payload

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['title'] = self.title
        payload['desc'] = self.message
        return payload
