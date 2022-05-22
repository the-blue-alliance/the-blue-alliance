import re
import unittest
from datetime import datetime

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator
from backend.tasks_io.models.notifications import MatchUpcomingNotification


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub", "urlfetch_stub")
class TestMatchUpcomingNotification(unittest.TestCase):
    def setUp(self):
        for team_number in range(7):
            Team(id="frc%s" % team_number, team_number=team_number).put()

        self.event = EventTestCreator.create_present_event()
        self.match = self.event.matches[0]

        self.notification = MatchUpcomingNotification(self.match)

    def test_type(self):
        assert MatchUpcomingNotification._type() == NotificationType.UPCOMING_MATCH

    def test_fcm_notification(self):
        # Set times for testing
        self.notification.match.time = None

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_predicted_time(self):
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:30.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_time(self):
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:00.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_short_name(self):
        self.notification.event.short_name = "Arizona North"
        # Set times for testing
        self.notification.match.time = None

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_short_name_predicted_time(self):
        self.notification.event.short_name = "Arizona North"
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:30.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_short_name_time(self):
        self.notification.event.short_name = "Arizona North"
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:00.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_data_payload(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        payload = self.notification.data_payload
        assert len(payload) == 2
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name

    def test_data_payload_team(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        team = Team.get_by_id("frc1")
        self.notification.team = team

        payload = self.notification.data_payload
        assert len(payload) == 3
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["team_key"] == team.key_name

    def test_webhook_message_data(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        payload = self.notification.webhook_message_data
        assert len(payload) == 7
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_keys"] is not None
        assert payload["scheduled_time"] is not None
        assert payload["predicted_time"] is not None
        assert payload["webcast"] is not None

    def test_webhook_message_data_none(self):
        self.notification.match.time = None
        self.notification.match.predicted_time = None
        self.notification.event._webcast = []

        payload = self.notification.webhook_message_data
        assert len(payload) == 4
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_keys"] is not None

    def test_webhook_message_data_team(self):
        self.notification.match.time = None
        self.notification.match.predicted_time = None
        self.notification.event._webcast = []

        team = Team.get_by_id("frc1")
        self.notification.team = team

        payload = self.notification.webhook_message_data

        assert len(payload) == 5
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["team_key"] == team.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_keys"] is not None

    def test_webhook_message_data_scheduled_time(self):
        self.notification.match.predicted_time = None
        self.notification.event._webcast = []

        payload = self.notification.webhook_message_data
        assert len(payload) == 5
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_keys"] is not None
        assert payload["scheduled_time"] is not None

    def test_webhook_message_data_predicted_time(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = None
        self.notification.event._webcast = []

        payload = self.notification.webhook_message_data
        assert len(payload) == 5
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_keys"] is not None
        assert payload["predicted_time"] is not None

    def test_webhook_message_data_webcasts(self):
        self.notification.match.time = None
        self.notification.match.predicted_time = None

        payload = self.notification.webhook_message_data
        assert len(payload) == 5
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == self.match.key_name
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_keys"] is not None
        assert payload["webcast"] is not None
