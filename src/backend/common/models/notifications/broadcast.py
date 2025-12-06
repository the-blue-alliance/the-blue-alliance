from typing import Any

from firebase_admin import messaging

from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.notification import Notification


class BroadcastNotification(Notification):
    def __init__(
        self,
        title: str,
        message: str,
        url: str | None = None,
        app_version: str | None = None,
    ) -> None:
        self.title = title
        self.message = message
        self.url = url
        self.app_version = app_version

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.BROADCAST

    @property
    def fcm_notification(self) -> messaging.Notification | None:
        return messaging.Notification(title=self.title, body=self.message)

    @property
    def data_payload(self) -> dict[str, str] | None:
        payload = {}

        if self.url:
            payload["url"] = self.url

        if self.app_version:
            payload["app_version"] = self.app_version

        return payload

    @property
    def webhook_message_data(self) -> dict[str, Any] | None:
        payload = {"title": self.title, "desc": self.message}

        if self.url:
            payload["url"] = self.url

        return payload
