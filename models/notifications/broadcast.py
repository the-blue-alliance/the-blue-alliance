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

        if self.app_version:
            payload['app_version'] = self.app_version

        return payload

    @property
    def webhook_message_data(self):
        payload = {
            'title': self.title,
            'desc': self.message
        }

        if self.url:
            payload['url'] = self.url

        return payload
