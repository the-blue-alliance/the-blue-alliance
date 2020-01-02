import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team

from tbans.consts.fcm.platform_priority import PlatformPriority
from tbans.models.notifications.alliance_selection import AllianceSelectionNotification


class TestAllianceSelectionNotification(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()

        self.testbed.init_taskqueue_stub(root_path=".")

        for team_number in range(7):
            Team(id="frc%s" % team_number,
                 team_number=team_number).put()

        self.event = EventTestCreator.createPresentEvent(id="2020testpresent")
        self.notification = AllianceSelectionNotification(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def test_type(self):
        self.assertEqual(AllianceSelectionNotification._type(), NotificationType.ALLIANCE_SELECTION)

    def test_platform_config(self):
        self.assertEqual(self.notification.platform_config.priority, PlatformPriority.HIGH)

    def test_fcm_notification(self):
        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Alliances Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'Present Test Event alliances have been updated.')

    def test_fcm_notification_short_name(self):
        self.notification.event.short_name = 'Arizona North'

        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Alliances Updated')
        self.assertEqual(self.notification.fcm_notification.body, 'Arizona North Regional alliances have been updated.')

    def test_data_payload(self):
        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload['event_key'], '2020testpresent')
        self.assertIsNotNone(payload['event'])

    def test_webhook_message_data(self):
        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload['event_key'], '2020testpresent')
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['event'])
