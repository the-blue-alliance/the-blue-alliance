import json
import re
import unittest
from datetime import datetime

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.match_upcoming import (
    MatchUpcomingNotification,
)
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator


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
        # Set times for testing (13:30 UTC = 8:30 EST)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.event.timezone_id = "America/New_York"

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 8:30 EST.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_predicted_time_no_timezone(self):
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.event.timezone_id = None

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
        # Set times for testing (13:00 UTC = 5:00 PST)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.event.timezone_id = "America/Los_Angeles"

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 5:00 PST.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_time_no_timezone(self):
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.event.timezone_id = None

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
        # Set times for testing (13:30 UTC = 6:30 MST)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.event.timezone_id = "America/Phoenix"

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 6:30 MST.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_short_name_time(self):
        self.notification.event.short_name = "Arizona North"
        # Set times for testing (13:00 UTC = 6:00 MST)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.event.timezone_id = "America/Phoenix"

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        match_regex = re.compile(
            r"^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 6:00 MST.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_invalid_timezone(self):
        # Test that an invalid timezone falls back gracefully (no timezone shown)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.event.timezone_id = "Invalid/Timezone"

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Q1 Starting Soon"
        )
        # With an invalid timezone, it should fall back to no timezone suffix
        match_regex = re.compile(
            r"^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:00.$"
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

    def test_fcm_notification_double_elim(self):
        import datetime as dt

        from google.appengine.ext import ndb

        from backend.common.consts.comp_level import CompLevel
        from backend.common.consts.event_type import EventType
        from backend.common.consts.playoff_type import PlayoffType
        from backend.common.manipulators.event_manipulator import EventManipulator
        from backend.common.manipulators.match_manipulator import MatchManipulator
        from backend.common.models.event import Event
        from backend.common.models.match import Match

        year = dt.datetime.now().year
        event = EventManipulator.createOrUpdate(
            Event(
                id="{}testde".format(year),
                event_short="testde",
                event_type_enum=EventType.REGIONAL,
                name="Double Elim Test Event",
                year=year,
                playoff_type=PlayoffType.DOUBLE_ELIM_8_TEAM,
            )
        )
        alliances = {
            "red": {"teams": ["frc1", "frc2", "frc3"], "score": -1},
            "blue": {"teams": ["frc4", "frc5", "frc6"], "score": -1},
        }
        match = MatchManipulator.createOrUpdate(
            Match(
                id="{}_sf1m1".format(event.key_name),
                event=ndb.Key(Event, event.key_name),
                year=year,
                comp_level=CompLevel.SF,
                set_number=1,
                match_number=1,
                team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
                alliances_json=json.dumps(alliances),
            )
        )
        notification = MatchUpcomingNotification(match)
        notification.match.time = None
        assert notification.fcm_notification is not None
        # For double elim, title should use "M1" (Match 1) not "SF1-1"
        assert notification.fcm_notification.title == "TESTDE M1 Starting Soon"
        # Body uses verbose_name which should also say "Match 1" for double elim
        assert "Match 1" in notification.fcm_notification.body
