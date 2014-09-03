from notifications.base_notification import BaseNotification


class PingNotification(BaseNotification):

    def _build_dict(self):
        data = {}
        data['message_type'] = 'ping'
        return data

    def _render_android(self):
        gcm_keys = self.keys[ClientType.OS_ANDROID]

        data = self._build_dict()

        return GCMMessage(gcm_keys, data)

    def _render_webhook(self):
        return self._build_dict()

