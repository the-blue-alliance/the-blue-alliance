import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from helpers.model_to_dict import ModelToDict
from notifications.alliance_selections import AllianceSelectionNotification


class TestAllianceNotification(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        # self.event = EventTestCreator.createPresentEvent()
        # self.notification = AllianceSelectionNotification(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def test_build(self):
        expected = {}
        # expected['message_type'] = NotificationType.type_names[NotificationType.ALLIANCE_SELECTION]
        # expected['message_data'] = {}
        # expected['message_data']['event'] = ModelToDict.matchConverter(self.event)

        # data = self.notification._build_dict()

        # Alliance notifications not ready yet
        # self.assertEqual(expected, data)
