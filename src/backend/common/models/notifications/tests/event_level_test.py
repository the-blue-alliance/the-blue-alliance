import json
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
        # 13:30 UTC = 8:30 EST
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title
            == "TESTPRESENT Qualification Matches Starting"
        )
        assert (
            self.notification.fcm_notification.body
            == "Qualification matches at the Present Test Event are scheduled for 8:30 EST."
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
        notification = EventLevelNotification(match)
        notification.match.time = None
        assert notification.fcm_notification is not None
        # For double elim, full_name should return "Playoff" not "Semifinals"
        assert notification.fcm_notification.title == "TESTDE Playoff Matches Starting"
        assert (
            notification.fcm_notification.body
            == "Playoff matches at the Double Elim Test Event are starting."
        )
