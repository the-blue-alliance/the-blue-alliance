import calendar
import logging
from typing import Any, cast, Dict, Optional

from pyre_extensions import none_throws

from backend.common.consts.notification_type import NotificationType
from backend.common.models.match import Match
from backend.tasks_io.models.notifications import Notification


class EventLevelNotification(Notification):
    def __init__(self, match: Match) -> None:
        self.match = match
        self.event = match.event.get()

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.LEVEL_STARTING

    @property
    def fcm_notification(self) -> Optional[Any]:
        if self.match.time:
            time = self.match.time.strftime("%H:%M")
            # Add timezone, if possible
            if self.event.timezone_id:
                try:
                    import pytz

                    timezone = pytz.timezone(self.event.timezone_id)
                    time += timezone.localize(self.match.time).strftime(" %Z")
                except Exception as e:
                    logging.warning(
                        f"Unable to add timezone to event level notification: {e}"
                    )
            ending = f"scheduled for {time}."
        else:
            ending = "starting."

        from firebase_admin import messaging

        return messaging.Notification(
            title="{} {} Matches Starting".format(
                self.event.event_short.upper(), self.match.full_name
            ),
            body="{} matches at the {} are {}".format(
                self.match.full_name, self.event.normalized_name, ending
            ),
        )

    @property
    def data_payload(self) -> Optional[Dict[str, str]]:
        return {"comp_level": self.match.comp_level, "event_key": self.event.key_name}

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        payload = cast(Dict[str, Any], none_throws(self.data_payload))
        payload["event_name"] = self.event.name
        if self.match.time:
            payload["scheduled_time"] = calendar.timegm(self.match.time.utctimetuple())
        return payload
