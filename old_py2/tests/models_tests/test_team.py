from datetime import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from models.event import Event
from models.team import Team


class TestTeam(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_championship_location(self):
        # No home_cmp, no updated
        team = Team(
            id="frc7332",
            team_number=7332
        )
        self.assertIsNone(team.home_cmp)
        self.assertIsNone(team.updated)
        self.assertIsNone(team.championship_location)

        # home_cmp, no updated
        team.home_cmp = 'cmp'
        self.assertIsNotNone(team.home_cmp)
        self.assertIsNone(team.updated)
        self.assertIsNone(team.championship_location)

        # no home_cmp, updated
        team.home_cmp = None
        team.updated = datetime.now()
        self.assertIsNone(team.home_cmp)
        self.assertIsNotNone(team.updated)
        self.assertIsNone(team.championship_location)

        # home_cmp, updated, no event
        team.home_cmp = 'cmp'
        self.assertIsNotNone(team.home_cmp)
        self.assertIsNotNone(team.updated)
        self.assertIsNone(team.championship_location)

        event = Event(
            id="{}{}".format(team.updated.year, team.home_cmp),
            event_type_enum=EventType.CMP_FINALS,
            event_short="cmp",
            year=team.updated.year
        )
        event.put()

        # home_cmp, updated, event, no city
        self.assertIsNotNone(team.home_cmp)
        self.assertIsNotNone(team.updated)
        self.assertIsNone(team.championship_location)

        # home_cmp, updated, event, city
        event.city = 'Atlanta'
        self.assertIsNotNone(team.home_cmp)
        self.assertIsNotNone(team.updated)
        self.assertEqual(team.championship_location, {team.updated.year: 'Atlanta'})
