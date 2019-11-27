from tbans.models.notifications.notification import Notification


class UpdateFavoritesNotification(Notification):

    def __init__(self, user_id):
        self.user_id = user_id

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.UPDATE_FAVORITES

    @property
    def platform_config(self):
        from tbans.models.fcm.platform_config import PlatformConfig
        return PlatformConfig(collapse_key='{}_favorite_update'.format(self.user_id))
