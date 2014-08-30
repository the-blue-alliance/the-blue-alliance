from consts.client_type import ClientType
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMMessage
from notifications.base_notification import BaseNotification


class UpdateSubscriptionsNotification(BaseNotification):

    def __init__(self, user_id):
        self.user_id = user_id

    def _render_android(self):
        user_collapse_key = "{}_subscriptions_update".format(self.user_id)
        clients = self.keys[ClientType.OS_ANDROID]

        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.UPDATE_FAVORITES]
        return GCMMessage(clients, data, collapse_key=user_collapse_key)

