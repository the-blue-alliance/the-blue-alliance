import unittest2
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from helpers.model_to_dict import ModelToDict
from models.team import Team
from notifications.match_score import UpcomingMatchNotification


class TestMatchScoreNotification(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub(root_path=".")

        for team_number in range(7):
            Team(id="frc%s" % team_number,
                 team_number=team_number).put()

        self.event = EventTestCreator.createPresentEvent()
        self.match = self.event.matches[0]
        self.notification = MatchScoreNotification(self.match)

    def tearDown(self):
        self.testbed.deactivate()

    def test_build(self):
        expected = {}
        expected['message_type'] = NotificationType.type_names[NotificationType.UPCOMING_MATCH]
        expected['message_data'] = {}
        expected['message_data']['event_name'] = self.event.name
        expected['message_data']['match_key'] = self.match.key_name
        expected['message_data']['team_keys'] = self.match.team_key_names
        expected['message_data']['scheduled_time'] = self.match.time
        expected['message_data']['predicted_time'] = self.match.time

        data = self.notification._build_dict()

        self.assertEqual(expected, data)
