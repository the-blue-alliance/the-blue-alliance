from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class BroadcastNotification(BaseNotification):

    def __init__(self, title, message, url):
        self.title = title
        self.message = message
        self.url = url

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.BROADCAST]
        data['message_data'] = {
            'title': self.title,
            'desc': self.message,
            'url': self.url,
        }
        return data
