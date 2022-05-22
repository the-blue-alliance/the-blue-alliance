from typing import Any, cast, Dict, Optional

from pyre_extensions import none_throws

from backend.common.consts.notification_type import NotificationType
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.tasks_io.models.notifications import Notification


class MatchVideoNotification(Notification):
    def __init__(self, match: Match, team: Optional[Team] = None) -> None:
        self.match = match
        self.event = match.event.get()
        self.team = team

    @classmethod
    def _type(cls) -> NotificationType:
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.MATCH_VIDEO

    @property
    def fcm_notification(self) -> Optional[Any]:
        title = self.event.event_short.upper()
        if self.team:
            title = "Team {}".format(self.team.team_number)

        body = [
            "Video for {} {}".format(
                self.event.event_short.upper(), self.match.verbose_name
            )
        ]
        if self.team:
            body.append("featuring Team {}".format(self.team.team_number))
        body.append("has been posted.")

        from firebase_admin import messaging

        return messaging.Notification(
            title="{} Match Video".format(title), body=" ".join(body)
        )

    @property
    def data_payload(self) -> Optional[Dict[str, str]]:
        payload = {"event_key": self.event.key_name, "match_key": self.match.key_name}

        if self.team:
            payload["team_key"] = self.team.key_name

        return payload

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        from backend.common.queries.dict_converters.match_converter import (
            MatchConverter,
        )

        payload = cast(Dict[str, Any], none_throws(self.data_payload))

        payload["event_name"] = self.event.name
        payload["match"] = MatchConverter.matchConverter_v3(self.match)
        return payload
