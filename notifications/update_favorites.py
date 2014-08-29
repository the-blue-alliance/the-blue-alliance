from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class UpdateFavoritesNotification(BaseNotification):

    def __init(self, user_id):
        self.user_id = user_id

    def _render_android(self):
        user_collapse_key = "{}_favorite_update".format(user_id)
        clients = self.keys[ClientType.OS_ANDROID]

        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.UPDATE_FAVORITES]
        return GCMMessage(clients, data, collapse_key=user_collapse_key)

