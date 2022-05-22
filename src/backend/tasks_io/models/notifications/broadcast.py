from typing import Any, Dict, Optional

from backend.common.consts.notification_type import NotificationType
from backend.tasks_io.models.notifications import Notification


class BroadcastNotification(Notification):
    def __init__(
        self,
        title: str,
        message: str,
        url: Optional[str] = None,
        app_version: Optional[str] = None,
    ) -> None:
        self.title = title
        self.message = message
        self.url = url
        self.app_version = app_version

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.BROADCAST

    @property
    def fcm_notification(self) -> Optional[Any]:
        from firebase_admin import messaging

        return messaging.Notification(title=self.title, body=self.message)

    @property
    def data_payload(self) -> Optional[Dict[str, str]]:
        payload = {}

        if self.url:
            payload["url"] = self.url

        if self.app_version:
            payload["app_version"] = self.app_version

        return payload

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        payload = {"title": self.title, "desc": self.message}

        if self.url:
            payload["url"] = self.url

        return payload
