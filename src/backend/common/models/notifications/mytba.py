from backend.common.consts.notification_type import NotificationType
from backend.common.models.fcm.platform_config import PlatformConfig
from backend.common.models.notifications.notification import Notification


class FavoritesUpdatedNotification(Notification):
    def __init__(self, user_id: str) -> None:
        super().__init__()
        self.user_id = user_id

    @classmethod
    def _type(cls) -> NotificationType:
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.UPDATE_FAVORITES

    @property
    def platform_config(self) -> PlatformConfig:
        return PlatformConfig(collapse_key=f"{self.user_id}_favorite_update")


class SubscriptionsUpdatedNotification(Notification):
    def __init__(self, user_id: str) -> None:
        super().__init__()
        self.user_id = user_id

    @classmethod
    def _type(cls) -> NotificationType:
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.UPDATE_SUBSCRIPTIONS

    @property
    def platform_config(self) -> PlatformConfig:
        return PlatformConfig(collapse_key=f"{self.user_id}_subscription_update")
