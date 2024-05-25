import unittest

import pytest

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.notification_type import NotificationType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.notifications.awards import AwardsNotification
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestAwardsNotification(unittest.TestCase):
    def setUp(self):
        self.event = Event(
            id="2020miket",
            event_type_enum=EventType.DISTRICT,
            short_name="Kettering University #1",
            name="FIM District Kettering University Event #1",
            event_short="miket",
            year=2020,
        )

        self.team = Team(id="frc7332", team_number=7332)

        self.award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.INDUSTRIAL_DESIGN),
            name_str="Industrial Design Award sponsored by General Motors",
            award_type_enum=AwardType.INDUSTRIAL_DESIGN,
            event=self.event.key,
            event_type_enum=EventType.DISTRICT,
            year=2020,
        )

        self.winner_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.WINNER),
            name_str="District Event Winner",
            award_type_enum=AwardType.WINNER,
            event=self.event.key,
            event_type_enum=EventType.DISTRICT,
            year=2020,
        )

    def test_type(self):
        assert AwardsNotification._type() == NotificationType.AWARDS

    def test_fcm_notification_event(self):
        notification = AwardsNotification(self.event)
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "MIKET Awards"
        assert (
            notification.fcm_notification.body
            == "2020 Kettering University #1 District awards have been posted."
        )

    def test_fcm_notification_team(self):
        self.award.team_list = [self.team.key]
        self.award.put()

        notification = AwardsNotification(self.event, self.team)

        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "Team 7332 Awards"
        assert (
            notification.fcm_notification.body
            == "Team 7332 won the Industrial Design Award sponsored by General Motors at the 2020 Kettering University #1 District."
        )

    def test_fcm_notification_team_winner(self):
        self.winner_award.team_list = [self.team.key]
        self.winner_award.put()

        notification = AwardsNotification(self.event, self.team)

        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "Team 7332 Awards"
        assert (
            notification.fcm_notification.body
            == "Team 7332 is the District Event Winner at the 2020 Kettering University #1 District."
        )

    def test_fcm_notification_team_finalist(self):
        self.winner_award.award_type_enum = AwardType.WINNER
        self.winner_award.name_str = "District Event Finalist"
        self.winner_award.team_list = [self.team.key]
        self.winner_award.put()

        notification = AwardsNotification(self.event, self.team)

        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "Team 7332 Awards"
        assert (
            notification.fcm_notification.body
            == "Team 7332 is the District Event Finalist at the 2020 Kettering University #1 District."
        )

    def test_fcm_notification_team_multiple(self):
        self.award.team_list = [self.team.key]
        self.award.put()
        self.winner_award.team_list = [self.team.key]
        self.winner_award.put()

        notification = AwardsNotification(self.event, self.team)

        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "Team 7332 Awards"
        assert (
            notification.fcm_notification.body
            == "Team 7332 won 2 awards at the 2020 Kettering University #1 District."
        )

    def test_data_payload(self):
        notification = AwardsNotification(self.event)
        # No `event_name`
        payload = notification.data_payload
        assert len(payload) == 1
        assert payload["event_key"] == "2020miket"

    def test_data_payload_team(self):
        notification = AwardsNotification(self.event, self.team)
        payload = notification.data_payload
        assert len(payload) == 2
        assert payload["event_key"] == "2020miket"
        assert payload["team_key"] == "frc7332"

    def test_webhook_message_data(self):
        self.award.put()
        self.winner_award.put()

        notification = AwardsNotification(self.event)

        payload = notification.webhook_message_data
        assert len(payload) == 3
        assert payload["event_key"] == "2020miket"
        assert payload["event_name"] == "FIM District Kettering University Event #1"
        assert payload["awards"] is not None
        assert len(payload["awards"]) == 2

    def test_webhook_message_data_team(self):
        self.award.team_list = [self.team.key]
        self.award.put()

        notification = AwardsNotification(self.event, self.team)

        payload = notification.webhook_message_data
        assert len(payload) == 4
        assert payload["event_key"] == "2020miket"
        assert payload["team_key"] == "frc7332"
        assert payload["event_name"] == "FIM District Kettering University Event #1"
        assert payload["awards"] is not None
        assert len(payload["awards"]) == 1
