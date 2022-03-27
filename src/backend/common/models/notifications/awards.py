from typing import Any, cast, Dict, Optional

from pyre_extensions import none_throws

from backend.common.consts.award_type import AwardType
from backend.common.consts.notification_type import NotificationType
from backend.common.models.event import Event
from backend.common.models.notifications.notification import Notification
from backend.common.models.team import Team


class AwardsNotification(Notification):
    def __init__(self, event: Event, team: Optional[Team] = None) -> None:
        self.event = event
        self.team = team
        self.team_awards = event.team_awards().get(team.key, []) if team else []

    @classmethod
    def _type(cls) -> NotificationType:
        from backend.common.consts.notification_type import NotificationType

        return NotificationType.AWARDS

    @property
    def fcm_notification(self) -> Optional[Any]:
        from firebase_admin import messaging

        # Construct Team-specific payload
        if self.team:
            if len(self.team_awards) == 1:
                award = self.team_awards[0]
                # For WINNER/FINALIST, change our verbage
                if award.award_type_enum in [AwardType.WINNER, AwardType.FINALIST]:
                    body = "is the"
                else:
                    body = "won the"
                body = "{} {}".format(body, award.name_str)
            else:
                body = "won {} awards".format(len(self.team_awards))
            return messaging.Notification(
                title="Team {} Awards".format(none_throws(self.team).team_number),
                body="Team {} {} at the {} {}.".format(
                    none_throws(self.team).team_number,
                    body,
                    self.event.year,
                    self.event.normalized_name,
                ),
            )

        # Construct Event payload
        return messaging.Notification(
            title="{} Awards".format(self.event.event_short.upper()),
            body="{} {} awards have been posted.".format(
                self.event.year, self.event.normalized_name
            ),
        )

    @property
    def data_payload(self) -> Optional[Dict[str, str]]:
        payload = {"event_key": self.event.key_name}

        if self.team:
            payload["team_key"] = self.team.key_name

        return payload

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        payload = cast(Dict[str, Any], none_throws(self.data_payload))
        payload["event_name"] = self.event.name

        from backend.common.helpers.award_helper import AwardHelper
        from backend.common.queries.dict_converters.award_converter import (
            AwardConverter,
        )

        if self.team:
            payload["awards"] = [
                AwardConverter.awardConverter_v3(award)
                for award in AwardHelper.organize_awards(self.team_awards)
            ]
        else:
            payload["awards"] = [
                AwardConverter.awardConverter_v3(award)
                for award in AwardHelper.organize_awards(self.event.awards)
            ]

        return payload
