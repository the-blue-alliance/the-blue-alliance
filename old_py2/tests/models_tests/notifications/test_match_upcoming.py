from datetime import datetime
import re
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team

from models.notifications.match_upcoming import MatchUpcomingNotification


class TestMatchUpcomingNotification(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        for team_number in range(7):
            Team(id="frc%s" % team_number,
                 team_number=team_number).put()

        self.event = EventTestCreator.createPresentEvent()
        self.match = self.event.matches[0]

        self.notification = MatchUpcomingNotification(self.match)

    def tearDown(self):
        self.testbed.deactivate()

    def test_type(self):
        self.assertEqual(MatchUpcomingNotification._type(), NotificationType.UPCOMING_MATCH)

    def test_fcm_notification(self):
        # Set times for testing
        self.notification.match.time = None

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Starting Soon')
        match_regex = re.compile(r'^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_fcm_notification_predicted_time(self):
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Starting Soon')
        match_regex = re.compile(r'^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:30.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_fcm_notification_time(self):
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Starting Soon')
        match_regex = re.compile(r'^Present Test Event Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:00.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_fcm_notification_short_name(self):
        self.notification.event.short_name = 'Arizona North'
        # Set times for testing
        self.notification.match.time = None

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Starting Soon')
        match_regex = re.compile(r'^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_fcm_notification_short_name_predicted_time(self):
        self.notification.event.short_name = 'Arizona North'
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Starting Soon')
        match_regex = re.compile(r'^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:30.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_fcm_notification_short_name_time(self):
        self.notification.event.short_name = 'Arizona North'
        # Set times for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Starting Soon')
        match_regex = re.compile(r'^Arizona North Regional Quals 1: \d+, \d+, \d+ will play \d+, \d+, \d+, scheduled for 13:00.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_data_payload(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        payload = self.notification.data_payload
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)

    def test_data_payload_team(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        team = Team.get_by_id('frc1')
        self.notification.team = team

        payload = self.notification.data_payload
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['team_key'], team.key_name)

    def test_webhook_message_data(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_webhook_message_data_none(self):
        self.notification.match.time = None
        self.notification.match.predicted_time = None
        self.notification.event._webcast = []

        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 4)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['team_keys'])

    def test_webhook_message_data_team(self):
        self.notification.match.time = None
        self.notification.match.predicted_time = None
        self.notification.event._webcast = []

        team = Team.get_by_id('frc1')
        self.notification.team = team

        payload = self.notification.webhook_message_data

        self.assertEqual(len(payload), 5)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['team_key'], team.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['team_keys'])

    def test_webhook_message_data_scheduled_time(self):
        self.notification.match.predicted_time = None
        self.notification.event._webcast = []

        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 5)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['scheduled_time'])

    def test_webhook_message_data_predicted_time(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = None
        self.notification.event._webcast = []

        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 5)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['predicted_time'])

    def test_webhook_message_data_webcasts(self):
        self.notification.match.time = None
        self.notification.match.predicted_time = None

        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 5)
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['match_key'], self.match.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['webcast'])
