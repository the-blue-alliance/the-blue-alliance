import unittest
from datetime import datetime

import pytest

from backend.common.consts.notification_type import NotificationType
from backend.common.models.team import Team
from backend.common.tests.creators.event_test_creator import EventTestCreator
from backend.tasks_io.tbans.models.notifications.event_schedule import (
    EventScheduleNotification,
)


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestEventScheduleNotification(unittest.TestCase):
    def _setup_notification(self):
        for team_number in range(7):
            Team(id="frc%s" % team_number, team_number=team_number).put()

        self.event = EventTestCreator.create_present_event()
        self.notification = EventScheduleNotification(self.event)

    def test_init(self):
        just_event = EventTestCreator.create_present_event(only_event=True)
        just_event_notification = EventScheduleNotification(just_event)
        assert just_event_notification.event == just_event
        assert just_event_notification.next_match is None

    def test_init_automatic_next(self):
        self._setup_notification()
        automatic_event_notification = EventScheduleNotification(self.event)
        assert automatic_event_notification.event == self.event
        assert automatic_event_notification.next_match is not None

    def test_init_explicit_next(self):
        self._setup_notification()
        explicit_match = self.event.matches[1]
        explicit_event_notification = EventScheduleNotification(
            self.event, explicit_match
        )
        assert explicit_event_notification.event == self.event
        assert explicit_event_notification.next_match == explicit_match

    def test_type(self):
        assert EventScheduleNotification._type() == NotificationType.SCHEDULE_UPDATED

    def test_fcm_notification(self):
        self._setup_notification()

        # Remove time for testing
        self.notification.next_match.time = None

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Schedule Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "The Present Test Event match schedule has been updated."
        )

    def test_fcm_notification_time(self):
        self._setup_notification()

        # Set constant scheduled time for testing
        self.notification.next_match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Schedule Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "The Present Test Event match schedule has been updated. The next match starts at 13:30."
        )

    def test_fcm_notification_time_timezone(self):
        self._setup_notification()

        self.event.timezone_id = "America/Detroit"
        # Set constant scheduled time for testing
        self.notification.next_match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Schedule Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "The Present Test Event match schedule has been updated. The next match starts at 13:30 EST."
        )

    def test_fcm_notification_short_name(self):
        self._setup_notification()

        self.notification.event.short_name = "Arizona North"
        # Remove time for testing
        self.notification.next_match.time = None

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Schedule Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "The Arizona North Regional match schedule has been updated."
        )

    def test_fcm_notification_short_name_time(self):
        self._setup_notification()

        self.notification.event.short_name = "Arizona North"
        # Set constant scheduled time for testing
        self.notification.next_match.time = datetime(2017, 11, 28, 13, 30, 59)

        assert self.notification.fcm_notification is not None
        assert (
            self.notification.fcm_notification.title == "TESTPRESENT Schedule Updated"
        )
        assert (
            self.notification.fcm_notification.body
            == "The Arizona North Regional match schedule has been updated. The next match starts at 13:30."
        )

    def test_data_payload(self):
        self._setup_notification()

        payload = self.notification.data_payload
        assert len(payload) == 1
        assert payload["event_key"] == "{}testpresent".format(self.event.year)

    def test_webhook_message_data(self):
        self._setup_notification()

        # Remove time for testing
        self.notification.next_match.time = None

        # Has `event_name`
        payload = self.notification.webhook_message_data
        assert len(payload) == 2
        assert payload["event_key"] == "{}testpresent".format(self.event.year)
        assert payload["event_name"] == "Present Test Event"

    def test_webhook_message_data_first_match_time(self):
        self._setup_notification()

        # Has `event_name`
        payload = self.notification.webhook_message_data
        assert len(payload) == 3
        assert payload["event_key"] == "{}testpresent".format(self.event.year)
        assert payload["event_name"] == "Present Test Event"
        assert payload["first_match_time"] is not None
