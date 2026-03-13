from typing import Any, cast, Dict, List, Optional

from pyre_extensions import none_throws

from backend.common.consts.notification_type import NotificationType
from backend.common.models.event import Event
from backend.common.models.notifications.notification import Notification
from backend.common.models.team import Team
from backend.common.queries.dict_converters.team_converter import TeamConverter


class EventTeamsNotification(Notification):
    def __init__(
        self, event: Event, added_teams: List[Team], removed_teams: List[Team]
    ) -> None:
        self.event = event
        self.added_teams = added_teams
        self.removed_teams = removed_teams

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.EVENT_TEAMS_UPDATED

    @property
    def fcm_notification(self) -> Optional[Any]:
        body = f"The {self.event.normalized_name} team list has been updated. "

        if self.added_teams:
            teams = ", ".join([team.team_number for team in self.added_teams])
            body += f"Teams added: {teams}. "

        if self.removed_teams:
            teams = ", ".join([team.team_number for team in self.removed_teams])
            body += f"Teams removed: {teams}. "

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
        payload["added_teams"] = [
            TeamConverter.teamConverter_v3(team) for team in self.added_teams
        ]
        payload["removed_teams"] = [
            TeamConverter.teamConverter_v3(team) for team in self.removed_teams
        ]
        return payload
