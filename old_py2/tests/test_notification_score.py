import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from helpers.model_to_dict import ModelToDict
from models.team import Team
from notifications.match_score import MatchScoreNotification


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

    def test_build(self):
        expected = {}
        expected['notification_type'] = NotificationType.type_names[NotificationType.MATCH_SCORE]
        expected['message_data'] = {}
        expected['message_data']['event_key'] = self.event.key_name
        expected['message_data']['event_name'] = self.event.name
        expected['message_data']['match'] = ModelToDict.matchConverter(self.match)

        data = self.notification._build_dict()

        self.assertEqual(expected, data)
