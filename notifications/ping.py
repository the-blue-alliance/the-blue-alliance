from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class PingNotification(BaseNotification):

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.PING]
        data['message_data'] = {'title': "Test Message",
                                'desc': "This is a test message ensuring your device can recieve push messages from The Blue Alliance."}
        return data
