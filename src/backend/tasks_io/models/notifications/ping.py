from typing import Any, Dict, Optional

from backend.common.consts.notification_type import NotificationType
from backend.tasks_io.models.notifications import Notification


class PingNotification(Notification):
    """A ping - used to make sure a client/webhook can recieve notifications properly"""

    _title = "Test Notification"
    _body = "This is a test message ensuring your device can recieve push messages from The Blue Alliance."

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.PING

    @property
    def fcm_notification(self) -> Optional[Any]:
        from firebase_admin import messaging

        return messaging.Notification(title=self._title, body=self._body)

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        return {
            "title": self._title,
            "desc": self._body,
        }
