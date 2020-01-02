from datetime import datetime
import re
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team

from tbans.consts.fcm.platform_priority import PlatformPriority
from tbans.models.notifications.match_upcoming import MatchUpcomingNotification


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

    def test_platform_config(self):
        self.assertEqual(self.notification.platform_config.priority, PlatformPriority.HIGH)

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

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_data_payload_time(self):
        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_data_payload_predicted_time(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = None

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_data_payload_no_time(self):
        self.notification.match.time = None

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_data_payload_no_webcast(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.event._webcast = []

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNone(payload['webcast'])

    def test_data_payload_time_no_webcast(self):
        self.notification.event._webcast = []

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNone(payload['webcast'])

    def test_data_payload_predicted_time_no_webcast(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = None
        self.notification.event._webcast = []

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNone(payload['webcast'])

    def test_data_payload_no_time_no_webcast(self):
        self.notification.match.time = None
        self.notification.event._webcast = []

        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 6)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNone(payload['webcast'])

    def test_webhook_message_data(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_webhook_message_data_time(self):
        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_webhook_message_data_predicted_time(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = None

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_webhook_message_data_no_time(self):
        self.notification.match.time = None

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNotNone(payload['webcast'])

    def test_webhook_message_data_no_webcast(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = datetime(2017, 11, 28, 13, 00, 59)
        self.notification.event._webcast = []

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNone(payload['webcast'])

    def test_webhook_message_data_time_no_webcast(self):
        self.notification.event._webcast = []

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNotNone(payload['scheduled_time'])
        self.assertIsNone(payload['webcast'])

    def test_webhook_message_data_predicted_time_no_webcast(self):
        self.notification.match.predicted_time = datetime(2017, 11, 28, 13, 30, 59)
        self.notification.match.time = None
        self.notification.event._webcast = []

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNotNone(payload['predicted_time'])
        self.assertIsNone(payload['webcast'])

    def test_webhook_message_data_no_time_no_webcast(self):
        self.notification.match.time = None
        self.notification.event._webcast = []

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 7)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertEqual(payload['match_key'], '{}testpresent_qm1'.format(self.event.year))
        self.assertIsNotNone(payload['team_keys'])
        self.assertIsNone(payload['scheduled_time'])
        self.assertIsNone(payload['predicted_time'])
        self.assertIsNone(payload['webcast'])
