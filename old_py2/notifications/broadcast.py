from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class BroadcastNotification(BaseNotification):

    _track_call = False

    def __init__(self, title, message, url, app_version=''):
        self.title = title
        self.message = message
        self.url = url
        self.app_version = app_version

    @property
    def _type(self):
        return NotificationType.BROADCAST

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {
            'title': self.title,
            'desc': self.message,
            'url': self.url,
        }

        if self.app_version:
            data['message_data']['app_version'] = self.app_version

        return data
