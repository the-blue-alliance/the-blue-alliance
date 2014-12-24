from consts.client_type import ClientType
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMMessage
from notifications.base_notification import BaseNotification


class UpdateFavoritesNotification(BaseNotification):

    _supported_clients = [ClientType.OS_ANDROID, ClientType.WEBHOOK] 

    def __init__(self, user_id, sending_device_key):
        self.user_id = user_id
        self.sending_device_key = sending_device_key

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.UPDATE_FAVORITES]
        return data

    def _render_android(self):
        user_collapse_key = "{}_favorite_update".format(self.user_id)

        if self.sending_device_key in self.keys[ClientType.OS_ANDROID]:
            self.keys[ClientType.OS_ANDROID].remove(self.sending_device_key)

        data = self._build_dict()
        return GCMMessage(self.keys[ClientType.OS_ANDROID], data, collapse_key=user_collapse_key)

