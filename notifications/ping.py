from consts.client_type import ClientType
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMMessage
from notifications.base_notification import BaseNotification


class PingNotification(BaseNotification):

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.PING]
        data['message_data'] = {'title': "Test Message",
                                'desc': "This is a test message ensuring your device can recieve push messages from The Blue Alliance."}
        return data

    def _render_android(self):
        gcm_keys = self.keys[ClientType.OS_ANDROID]
        data = self._build_dict()

        return GCMMessage(gcm_keys, data)

    def _render_webhook(self):
        return self._build_dict()

