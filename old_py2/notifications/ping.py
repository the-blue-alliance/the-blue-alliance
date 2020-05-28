from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class PingNotification(BaseNotification):

    _track_call = False

    @property
    def _type(self):
        return NotificationType.PING

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {'title': "Test Message",
                                'desc': "This is a test message ensuring your device can recieve push messages from The Blue Alliance."}
        return data
