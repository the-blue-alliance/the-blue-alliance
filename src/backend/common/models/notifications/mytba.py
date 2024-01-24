from typing import Optional

from backend.common.consts.client_type import ClientType
from backend.common.consts.notification_type import (
    NotificationType,
    TYPE_NAMES as NOTIFICATION_TYPE_NAMES,
)
from backend.common.models.fcm.platform_config import PlatformConfig
from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.notification import Notification


class MyTbaBaseNotification(Notification):
    def __init__(self, user_id: str, initiating_device_id: Optional[str]) -> None:
        super().__init__()
        self.user_id = user_id
        self.initiating_device_id = initiating_device_id

    def should_send_to_client(self, client: MobileClient) -> bool:
        """
        The mytba notifications have two special aspects of behavior:
         (1) we omit sending the notification back to the same device which made the change
         (2) we do not send them to webhook clients
        """
        if client.client_type == ClientType.WEBHOOK:
            return False

        if (
            self.initiating_device_id is not None
            and self.initiating_device_id == client.device_uuid
        ):
            return False

        return True

    @property
    def platform_config(self) -> PlatformConfig:
        notification_type_name = NOTIFICATION_TYPE_NAMES[self._type()]
        return PlatformConfig(collapse_key=f"{self.user_id}_{notification_type_name}")


class FavoritesUpdatedNotification(MyTbaBaseNotification):
    @classmethod
    def _type(cls) -> NotificationType:
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.UPDATE_FAVORITES


class SubscriptionsUpdatedNotification(MyTbaBaseNotification):
    @classmethod
    def _type(cls) -> NotificationType:
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.UPDATE_SUBSCRIPTIONS
