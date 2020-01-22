import re
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team

from models.notifications.match_score import MatchScoreNotification


class TestMatchScoreNotification(unittest2.TestCase):

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

        self.notification = MatchScoreNotification(self.match)

    def tearDown(self):
        self.testbed.deactivate()

    def test_type(self):
        self.assertEqual(MatchScoreNotification._type(), NotificationType.MATCH_SCORE)

    def test_fcm_notification(self):
        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Results')
        match_regex = re.compile(r'^\d+, \d+, \d+ beat \d+, \d+, \d+ scoring \d+-\d+.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_fcm_notification_tied(self):
        score = self.notification.match.alliances['red']['score']
        self.notification.match.alliances['blue']['score'] = score
        self.assertIsNotNone(self.notification.fcm_notification)
        self.assertEqual(self.notification.fcm_notification.title, 'TESTPRESENT Q1 Results')
        match_regex = re.compile(r'^\d+, \d+, \d+ tied with \d+, \d+, \d+ scoring \d+-\d+.$')
        match = re.match(match_regex, self.notification.fcm_notification.body)
        self.assertIsNotNone(match)

    def test_data_payload(self):
        # No `event_name`
        payload = self.notification.data_payload
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertIsNotNone(payload['match'])

    def test_webhook_message_data(self):
        # Has `event_name`
        payload = self.notification.webhook_message_data
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload['event_key'], '{}testpresent'.format(self.event.year))
        self.assertEqual(payload['event_name'], 'Present Test Event')
        self.assertIsNotNone(payload['match'])
