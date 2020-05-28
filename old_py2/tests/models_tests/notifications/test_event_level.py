from datetime import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team

from models.notifications.event_level import EventLevelNotification


class TestEventLevelNotification(unittest2.TestCase):

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

        self.notification = EventLevelNotification(self.match)

    def tearDown(self):
        self.testbed.deactivate()

    def test_type(self):
        self.assertEqual(EventLevelNotification._type(), NotificationType.LEVEL_STARTING)

    def test_fcm_notification(self):
        # Remove time for testing
        self.notification.match.time = None

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Qualification Matches Starting')
        self.assertEqual(self.notification.fcm_notification.body, 'Qualification matches at the Present Test Event are starting.')

    def test_fcm_notification_short_name(self):
        self.notification.event.short_name = 'Arizona North'
        # Remove time for testing
        self.notification.match.time = None

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Qualification Matches Starting')
        self.assertEqual(self.notification.fcm_notification.body, 'Qualification matches at the Arizona North Regional are starting.')

    def test_fcm_notification_scheduled_time(self):
        # Set constant scheduled time for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Qualification Matches Starting')
        self.assertEqual(self.notification.fcm_notification.body, 'Qualification matches at the Present Test Event are scheduled for 13:30.')

    def test_fcm_notification_scheduled_time_timezone(self):
        self.notification.event.timezone_id = 'America/Detroit'
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Qualification Matches Starting')
        self.assertEqual(self.notification.fcm_notification.body, 'Qualification matches at the Present Test Event are scheduled for 13:30 EST.')

    def test_fcm_notification_short_name_scheduled_time(self):
        self.notification.event.short_name = 'Arizona North'
        # Set constant scheduled time for testing
        self.notification.match.time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Qualification Matches Starting')
        self.assertEqual(self.notification.fcm_notification.body, 'Qualification matches at the Arizona North Regional are scheduled for 13:30.')

    def test_data_payload(self):
        # Remove time for testing
        self.notification.match.time = None

        payload = self.notification.data_payload
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload['comp_level'], 'qm')
        self.assertEqual(payload['event_key'], self.event.key_name)

    def test_webhook_message_data(self):
        # Remove time for testing
        self.notification.match.time = None

        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload['comp_level'], 'qm')
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')

    def test_webhook_message_data_scheduled_time(self):
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 4)
        self.assertEqual(payload['comp_level'], 'qm')
        self.assertEqual(payload['event_key'], self.event.key_name)
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['scheduled_time'])
