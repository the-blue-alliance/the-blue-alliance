from models.notifications.notification import Notification


class UpdateMyTBANotification(Notification):

    def __init__(self, user_id):
        self.user_id = user_id

    @property
    def platform_config(self):
        from consts.notification_type import NotificationType
        from models.fcm.platform_config import PlatformConfig
        return PlatformConfig(collapse_key='{}_{}'.format(self.user_id, NotificationType.type_names[self.__class__._type()]))
