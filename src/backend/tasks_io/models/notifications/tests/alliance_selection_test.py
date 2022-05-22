import unittest

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.event_details import EventDetails
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator
from backend.tasks_io.models.notifications import AllianceSelectionNotification


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestAllianceSelectionNotification(unittest.TestCase):
    def setUp(self) -> None:
        for team_number in range(7):
            Team(id="frc%s" % team_number, team_number=team_number).put()

        self.event = EventTestCreator.create_present_event()
        self.notification = AllianceSelectionNotification(self.event)

    def test_type(self):
        assert (
            AllianceSelectionNotification._type() == NotificationType.ALLIANCE_SELECTION
        )

    def test_fcm_notification(self):
        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Alliances Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "Present Test Event alliances have been updated."
        )

    def test_fcm_notification_team_captain(self):
        team = Team.get_by_id("frc1")
        # Setup alliance selection information
        EventDetails(
            id=self.event.key_name,
            alliance_selections=[{"declines": [], "picks": ["frc1", "frc2", "frc3"]}],
        ).put()

        notification = AllianceSelectionNotification(self.event, team)
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "TESTPRESENT Alliances Updated"
        assert (
            notification.fcm_notification.body
            == "Present Test Event alliances have been updated. Team 1 is Captain of Alliance 1 with Team 2 and Team 3."
        )

    def test_fcm_notification_team(self):
        team = Team.get_by_id("frc1")
        # Setup alliance selection information
        EventDetails(
            id=self.event.key_name,
            alliance_selections=[{"declines": [], "picks": ["frc2", "frc1", "frc3"]}],
        ).put()

        notification = AllianceSelectionNotification(self.event, team)
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "TESTPRESENT Alliances Updated"
        assert (
            notification.fcm_notification.body
            == "Present Test Event alliances have been updated. Team 1 is on Alliance 1 with Team 2 and Team 3."
        )

    def test_fcm_notification_team_four(self):
        team = Team.get_by_id("frc1")
        # Setup alliance selection information
        EventDetails(
            id=self.event.key_name,
            alliance_selections=[
                {"declines": [], "picks": ["frc2", "frc1", "frc3", "frc4"]}
            ],
        ).put()

        notification = AllianceSelectionNotification(self.event, team)
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "TESTPRESENT Alliances Updated"
        assert (
            notification.fcm_notification.body
            == "Present Test Event alliances have been updated. Team 1 is on Alliance 1 with Team 2, Team 3 and Team 4."
        )

    def test_fcm_notification_short_name(self):
        self.notification.event.short_name = "Arizona North"

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Alliances Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "Arizona North Regional alliances have been updated."
        )

    def test_data_payload(self):
        payload = self.notification.data_payload
        assert len(payload) == 1
        assert payload["event_key"] == self.event.key_name

    def test_data_payload_team(self):
        team = Team.get_by_id("frc1")
        notification = AllianceSelectionNotification(self.event, team)
        payload = notification.data_payload
        assert len(payload) == 2
        assert payload["event_key"] == self.event.key_name
        assert payload["team_key"] == team.key_name

    def test_webhook_message_data(self):
        payload = self.notification.webhook_message_data
        assert len(payload) == 3
        assert payload["event_key"] == self.event.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["event"] is not None

    def test_webhook_message_data_team(self):
        team = Team.get_by_id("frc1")
        notification = AllianceSelectionNotification(self.event, team)
        payload = notification.webhook_message_data
        assert len(payload) == 4
        assert payload["event_key"] == self.event.key_name
        assert payload["team_key"] == team.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["event"] is not None
