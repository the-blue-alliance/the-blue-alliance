import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event.event_test_creator import EventTestCreator

from models.team import Team


class TestEventTeamCreator(unittest2.TestCase):
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

        self.events = []

    def tearDown(self):
        for event in self.events:
            event.key.delete()

        self.testbed.deactivate()

    def test_creates(self):
        self.events.append(EventTestCreator.createPastEvent())
        self.events.append(EventTestCreator.createFutureEvent())
        self.events.append(EventTestCreator.createPresentEvent())

        # TODO: assert the events got created properly -gregmarra 20130416
