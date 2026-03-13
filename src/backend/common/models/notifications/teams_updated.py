from typing import Any, cast, Dict, Optional

from pyre_extensions import none_throws

from backend.common.consts.notification_type import NotificationType
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.notifications.notification import Notification


class EventTeamsNotification(Notification):
    def __init__(self, event: Event) -> None:
        self.event = event

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.EVENT_TEAMS_UPDATED

    @property
    def fcm_notification(self) -> Optional[Any]:
        body = f"The {self.event.normalized_name} team list has been updated."
        
        from firebase_admin import messaging

        return messaging.Notification(
            title="{} Teams Updated".format(self.event.event_short.upper()),
            body=body,
        )

    @property
    def data_payload(self) -> Optional[Dict[str, str]]:
        return {"event_key": self.event.key_name}

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        payload = cast(Dict[str, Any], none_throws(self.data_payload))
        payload["event_name"] = self.event.name
        return payload
