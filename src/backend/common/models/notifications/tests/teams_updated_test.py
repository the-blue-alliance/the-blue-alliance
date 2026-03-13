import unittest

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.teams_updated import EventTeamsNotification
from backend.common.models.team import Team
from backend.common.queries.dict_converters.team_converter import TeamConverter
from backend.common.tests.creators.event_test_creator import EventTestCreator


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestEventTeamUpdateNotification(unittest.TestCase):
    def setUp(self) -> None:
        for team_number in range(7):
            Team(id="frc%s" % team_number, team_number=team_number).put()

        self.event = EventTestCreator.create_present_event()
        self.notification = EventTeamsNotification(
            self.event, added_teams=[], removed_teams=[]
        )

    def test_type(self):
        assert EventTeamsNotification._type() == NotificationType.EVENT_TEAMS_UPDATED

    def test_fcm_notification(self):
        assert self.notification.fcm_notification is not None
        assert self.notification.fcm_notification.title == "TESTPRESENT Teams Updated"
        assert (
            self.notification.fcm_notification.body
            == "The Present Test Event team list has been updated."
        )

    def test_fcm_notification_additions(self):
        team1 = Team.get_by_id("frc1")
        team2 = Team.get_by_id("frc2")
        notification = EventTeamsNotification(
            self.event, added_teams=[team1, team2], removed_teams=[]
        )
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "TESTPRESENT Teams Updated"
        assert (
            notification.fcm_notification.body
            == "The Present Test Event team list has been updated. Teams added: 1, 2."
        )

    def test_fcm_notification_removals(self):
        team1 = Team.get_by_id("frc1")
        team2 = Team.get_by_id("frc2")
        notification = EventTeamsNotification(
            self.event, added_teams=[], removed_teams=[team1, team2]
        )
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "TESTPRESENT Teams Updated"
        assert (
            notification.fcm_notification.body
            == "The Present Test Event team list has been updated. Teams removed: 1, 2."
        )

    def test_fcm_notification_additions_and_removals(self):
        team1 = Team.get_by_id("frc1")
        team2 = Team.get_by_id("frc2")
        team3 = Team.get_by_id("frc3")
        team4 = Team.get_by_id("frc4")
        notification = EventTeamsNotification(
            self.event, added_teams=[team1, team2], removed_teams=[team3, team4]
        )
        assert notification.fcm_notification is not None
        assert notification.fcm_notification.title == "TESTPRESENT Teams Updated"
        assert (
            notification.fcm_notification.body
            == "The Present Test Event team list has been updated. Teams added: 1, 2. Teams removed: 3, 4."
        )

    def test_data_payload(self):
        payload = self.notification.data_payload
        assert len(payload) == 1

    def test_webhook_message_data(self):
        payload = self.notification.webhook_message_data
        assert len(payload) == 4
        assert payload["event_key"] == self.event.key_name
        assert payload["event_name"] == self.event.name
        assert payload["added_teams"] == []
        assert payload["removed_teams"] == []

    def test_webhook_message_data_additions_and_removals(self):
        team1 = Team.get_by_id("frc1")
        team2 = Team.get_by_id("frc2")
        team3 = Team.get_by_id("frc3")
        team4 = Team.get_by_id("frc4")
        notification = EventTeamsNotification(
            self.event, added_teams=[team1, team2], removed_teams=[team3, team4]
        )
        payload = notification.webhook_message_data
        assert len(payload) == 4
        assert payload["event_key"] == self.event.key_name
        assert payload["event_name"] == self.event.name
        assert payload["added_teams"] == [
            TeamConverter.teamConverter_v3(team1),
            TeamConverter.teamConverter_v3(team2),
        ]
        assert payload["removed_teams"] == [
            TeamConverter.teamConverter_v3(team3),
            TeamConverter.teamConverter_v3(team4),
        ]
