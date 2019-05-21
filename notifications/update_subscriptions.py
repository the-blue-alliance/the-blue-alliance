import logging

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class UpdateSubscriptionsNotification(BaseNotification):

    _supported_clients = [ClientType.OS_ANDROID, ClientType.OS_IOS, ClientType.WEBHOOK]
    _track_call = False

    def __init__(self, user_id, sending_device_key):
        self.user_id = user_id
        self.sending_device_key = sending_device_key

    @property
    def _type(self):
        return NotificationType.UPDATE_SUBSCRIPTIONS

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        return data

    def _render_android(self):
        from controllers.gcm.gcm import GCMMessage
        user_collapse_key = "{}_subscriptions_update".format(self.user_id)

        if self.sending_device_key in self.keys[ClientType.OS_ANDROID]:
            self.keys[ClientType.OS_ANDROID].remove(self.sending_device_key)

        data = self._build_dict()
        return GCMMessage(self.keys[ClientType.OS_ANDROID], data, collapse_key=user_collapse_key)
