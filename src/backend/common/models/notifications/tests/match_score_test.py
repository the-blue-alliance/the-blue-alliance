import json
import re
import unittest

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.notifications.match_score import (
    MatchScoreNotification,
)
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestMatchScoreNotification(unittest.TestCase):
    def setUp(self):
        for team_number in range(6):
            Team(id="frc%s" % team_number, team_number=team_number).put()

        self.event = EventTestCreator.create_present_event()
        self.match = self.event.matches[0]

        self.notification = MatchScoreNotification(self.match)

    def test_type(self):
        assert MatchScoreNotification._type() == NotificationType.MATCH_SCORE

    def test_fcm_notification(self):
        assert self.notification.fcm_notification is not None
        assert self.notification.fcm_notification.title == "TESTPRESENT Q1 Results"
        match_regex = re.compile(r"^\d+, \d+, \d+ beat \d+, \d+, \d+ scoring \d+-\d+.$")
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_tied(self):
        score = self.notification.match.alliances["red"]["score"]
        self.notification.match.alliances["blue"]["score"] = score
        assert self.notification.fcm_notification is not None
        assert self.notification.fcm_notification.title == "TESTPRESENT Q1 Results"
        match_regex = re.compile(
            r"^\d+, \d+, \d+ tied with \d+, \d+, \d+ scoring \d+-\d+.$"
        )
        match = re.match(match_regex, self.notification.fcm_notification.body)
        assert match is not None

    def test_fcm_notification_team(self):
        team = Team.get_by_id("frc1")
        notification = MatchScoreNotification(self.match, team)
        assert notification.fcm_notification.title == "Team 1 TESTPRESENT Q1 Results"

    def test_fcm_notification_double_elim(self):
        import datetime

        from google.appengine.ext import ndb

        from backend.common.consts.comp_level import CompLevel
        from backend.common.consts.event_type import EventType
        from backend.common.consts.playoff_type import PlayoffType
        from backend.common.manipulators.event_manipulator import EventManipulator
        from backend.common.manipulators.match_manipulator import MatchManipulator
        from backend.common.models.event import Event
        from backend.common.models.match import Match

        year = datetime.datetime.now().year
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
            "red": {"teams": ["frc1", "frc2", "frc3"], "score": 100},
            "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 50},
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
        notification = MatchScoreNotification(match)
        assert notification.fcm_notification is not None
        # For double elim, title should use "M1" (Match 1) not "SF1-1"
        assert notification.fcm_notification.title == "TESTDE M1 Results"

    def test_data_payload(self):
        payload = self.notification.data_payload
        assert len(payload) == 2
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == "{}_qm1".format(self.event.key_name)

    def test_data_payload_team(self):
        team = Team.get_by_id("frc1")
        notification = MatchScoreNotification(self.match, team)
        payload = notification.data_payload
        assert len(payload) == 3
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == "{}_qm1".format(self.event.key_name)
        assert payload["team_key"] == "frc1"

    def test_webhook_message_data(self):
        # Has `event_name`
        payload = self.notification.webhook_message_data
        assert len(payload) == 4
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == "{}_qm1".format(self.event.key_name)
        assert payload["event_name"] == "Present Test Event"
        assert payload["match"] is not None

    def test_webhook_message_data_team(self):
        team = Team.get_by_id("frc1")
        notification = MatchScoreNotification(self.match, team)
        payload = notification.webhook_message_data
        assert len(payload) == 5
        assert payload["event_key"] == self.event.key_name
        assert payload["match_key"] == "{}_qm1".format(self.event.key_name)
        assert payload["event_name"] == "Present Test Event"
        assert payload["team_key"] == "frc1"
        assert payload["match"] is not None
