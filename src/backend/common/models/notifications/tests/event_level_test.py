import unittest
from datetime import datetime

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.event_level import (
    EventLevelNotification,
)
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestEventLevelNotification(unittest.TestCase):
    def setUp(self):
        for team_number in range(7):
            Team(id="frc%s" % team_number, team_number=team_number).put()

        self.event = EventTestCreator.create_present_event()
        self.match = self.event.matches[0]

        self.notification = EventLevelNotification(self.match)

    def test_type(self):
        self.assertEqual(
            EventLevelNotification._type(), NotificationType.LEVEL_STARTING
        )

    def test_fcm_notification(self):
        # Remove time for testing
        self.notification.match.time = None

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title
            == "TESTPRESENT Qualification Matches Starting"
        )
        assert (
            self.notification.fcm_notification.body
            == "Qualification matches at the Present Test Event are starting."
        )

    def test_fcm_notification_short_name(self):
        self.notification.event.short_name = "Arizona North"
        # Remove time for testing
        self.notification.match.time = None

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title
            == "TESTPRESENT Qualification Matches Starting"
        )
        assert (
            self.notification.fcm_notification.body
            == "Qualification matches at the Arizona North Regional are starting."
        )

    def test_fcm_notification_scheduled_time(self):
        # Set constant scheduled time for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title
            == "TESTPRESENT Qualification Matches Starting"
        )
        assert (
            self.notification.fcm_notification.body
            == "Qualification matches at the Present Test Event are scheduled for 13:30."
        )

    def test_fcm_notification_scheduled_time_timezone(self):
        self.notification.event.timezone_id = "America/Detroit"
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title
            == "TESTPRESENT Qualification Matches Starting"
        )
        assert (
            self.notification.fcm_notification.body
            == "Qualification matches at the Present Test Event are scheduled for 13:30 EST."
        )

    def test_fcm_notification_short_name_scheduled_time(self):
        self.notification.event.short_name = "Arizona North"
        # Set constant scheduled time for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title
            == "TESTPRESENT Qualification Matches Starting"
        )
        assert (
            self.notification.fcm_notification.body
            == "Qualification matches at the Arizona North Regional are scheduled for 13:30."
        )

    def test_data_payload(self):
        # Remove time for testing
        self.notification.match.time = None

        payload = self.notification.data_payload
        assert len(payload) == 2
        assert payload["comp_level"] == "qm"
        assert payload["event_key"] == self.event.key_name

    def test_webhook_message_data(self):
        # Remove time for testing
        self.notification.match.time = None

        payload = self.notification.webhook_message_data
        assert len(payload) == 3
        assert payload["comp_level"] == "qm"
        assert payload["event_key"] == self.event.key_name
        assert payload["event_name"] == "Present Test Event"

    def test_webhook_message_data_scheduled_time(self):
        payload = self.notification.webhook_message_data
        assert len(payload) == 4
        assert payload["comp_level"] == "qm"
        assert payload["event_key"] == self.event.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["scheduled_time"] is not None
