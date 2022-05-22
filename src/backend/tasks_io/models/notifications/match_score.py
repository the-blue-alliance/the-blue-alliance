from typing import Any, cast, Dict, Optional

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.notification_type import NotificationType
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.tasks_io.models.notifications import Notification


class MatchScoreNotification(Notification):
    def __init__(self, match: Match, team: Optional[Team] = None) -> None:
        self.match = match
        self.event = match.event.get()
        self.team = team

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.MATCH_SCORE

    @property
    def fcm_notification(self) -> Optional[Any]:
        if self.match.winning_alliance == "":
            alliance_one = self.match.alliances[AllianceColor.RED]
        else:
            alliance_one = self.match.alliances[
                cast(AllianceColor, self.match.winning_alliance)
            ]

        if self.match.losing_alliance == "":
            alliance_two = self.match.alliances[AllianceColor.BLUE]
        else:
            alliance_two = self.match.alliances[
                cast(AllianceColor, self.match.losing_alliance)
            ]

        # [3:] to remove 'frc' prefix
        alliance_one_teams = ", ".join([team[3:] for team in alliance_one["teams"]])
        alliance_two_teams = ", ".join([team[3:] for team in alliance_two["teams"]])

        alliance_one_score = alliance_one["score"]
        alliance_two_score = alliance_two["score"]
        if alliance_one_score == alliance_two_score:
            action = "tied with"
        else:
            action = "beat"

        title = self.event.event_short.upper()
        if self.team:
            title = "Team {} {}".format(self.team.team_number, title)

        from firebase_admin import messaging

        return messaging.Notification(
            title="{} {} Results".format(title, self.match.short_name),
            body="{} {} {} scoring {}-{}.".format(
                alliance_one_teams,
                action,
                alliance_two_teams,
                alliance_one_score,
                alliance_two_score,
            ),
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
