from datetime import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team

from models.notifications.event_schedule import EventScheduleNotification


class TestEventScheduleNotification(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

    def tearDown(self):
        self.testbed.deactivate()

    def _setup_notification(self):
        for team_number in range(7):
            Team(id="frc%s" % team_number,
                 team_number=team_number).put()

        self.event = EventTestCreator.createPresentEvent()
        self.notification = EventScheduleNotification(self.event)

    def test_init(self):
        just_event = EventTestCreator.createPresentEvent(only_event=True)
        just_event_notification = EventScheduleNotification(just_event)
        self.assertEqual(just_event_notification.event, just_event)
        self.assertIsNone(just_event_notification.next_match)

    def test_init_automatic_next(self):
        self._setup_notification()
        automatic_event_notification = EventScheduleNotification(self.event)
        self.assertEqual(automatic_event_notification.event, self.event)
        self.assertIsNotNone(automatic_event_notification.next_match)

    def test_init_explicit_next(self):
        self._setup_notification()
        explicit_match = self.event.matches[1]
        explicit_event_notification = EventScheduleNotification(self.event, explicit_match)
        self.assertEqual(explicit_event_notification.event, self.event)
        self.assertEqual(explicit_event_notification.next_match, explicit_match)

    def test_type(self):
        self.assertEqual(EventScheduleNotification._type(), NotificationType.SCHEDULE_UPDATED)

    def test_fcm_notification(self):
        self._setup_notification()

        # Remove time for testing
        self.notification.next_match.time = None

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Schedule Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'The Present Test Event match schedule has been updated.')

    def test_fcm_notification_time(self):
        self._setup_notification()

        # Set constant scheduled time for testing
        self.notification.next_match.time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Schedule Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'The Present Test Event match schedule has been updated. The next match starts at 13:30.')

    def test_fcm_notification_time_timezone(self):
        self._setup_notification()

        self.event.timezone_id = 'America/Detroit'
        # Set constant scheduled time for testing
        self.notification.next_match.time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Schedule Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'The Present Test Event match schedule has been updated. The next match starts at 13:30 EST.')

    def test_fcm_notification_short_name(self):
        self._setup_notification()

        self.notification.event.short_name = 'Arizona North'
        # Remove time for testing
        self.notification.next_match.time = None

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Schedule Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'The Arizona North Regional match schedule has been updated.')

    def test_fcm_notification_short_name_time(self):
        self._setup_notification()

        self.notification.event.short_name = 'Arizona North'
        # Set constant scheduled time for testing
        self.notification.next_match.time = datetime(2017, 11, 28, 13, 30, 59)

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Schedule Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'The Arizona North Regional match schedule has been updated. The next match starts at 13:30.')

    def test_data_payload(self):
        self._setup_notification()

        payload = self.notification.data_payload
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))

    def test_webhook_message_data(self):
        self._setup_notification()

        # Remove time for testing
        self.notification.next_match.time = None

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')

    def test_webhook_message_data_first_match_time(self):
        self._setup_notification()

        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['first_match_time'])
