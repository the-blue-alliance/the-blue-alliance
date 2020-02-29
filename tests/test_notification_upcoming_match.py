import calendar
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from helpers.event.event_test_creator import EventTestCreator
from models.team import Team
from notifications.upcoming_match import UpcomingMatchNotification


class TestUpcomingMatchNotification(unittest2.TestCase):
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
        self.match.predicted_time = self.match.time
        self.notification = UpcomingMatchNotification(self.match, self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def test_build(self):
        expected = {}
        self.maxDiff = None
        expected['notification_type'] = NotificationType.type_names[NotificationType.UPCOMING_MATCH]
        expected['message_data'] = {}
        expected['message_data']['event_key'] = self.event.key_name
        expected['message_data']['event_name'] = self.event.name
        expected['message_data']['match_key'] = self.match.key_name
        expected['message_data']['team_keys'] = self.match.team_key_names

        if self.match.time:
            expected['message_data']['scheduled_time'] = calendar.timegm(self.match.time.utctimetuple())
        else:
            expected['message_data']['scheduled_time'] = None

        expected['message_data']['predicted_time'] = expected['message_data']['scheduled_time']

        expected['message_data']['webcast'] = {
            'channel': '6540154',
            'status': 'unknown',
            'stream_title': None,
            'type': 'ustream',
            'viewer_count': None,
        }

        data = self.notification._build_dict()

        self.assertEqual(expected, data)
