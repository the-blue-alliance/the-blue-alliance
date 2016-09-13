import datetime
import unittest2

from consts.event_type import EventType

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event_team_manipulator import EventTeamManipulator
from helpers.event_team_repairer import EventTeamRepairer

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class TestEventTeamRepairer(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        event = Event(
            id="2011ct",
            end_date=datetime.datetime(2011, 4, 2, 0, 0),
            event_short="ct",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Northeast Utilities FIRST Connecticut Regional",
            start_date=datetime.datetime(2011, 3, 31, 0, 0),
            year=2011,
            venue_address="Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website="http://www.ctfirst.org/ctr"
        )
        event.put()

        team = Team(
            id="frc177",
            team_number=177,
            website="http://www.bobcatrobotics.org"
        )
        team.put()

        event_team = EventTeam(
            id="%s_%s" % (event.key.id(), team.key.id()),
            event=event.key,
            team=team.key,
            year=None)
        event_team.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_repair(self):
        event_team = EventTeam.get_by_id("2011ct_frc177")
        self.assertEqual(event_team.year, None)

        broken_event_teams = EventTeam.query(EventTeam.year == None).fetch()
        self.assertGreater(len(broken_event_teams), 0)

        fixed_event_teams = EventTeamRepairer.repair(broken_event_teams)
        fixed_event_teams = EventTeamManipulator.createOrUpdate(fixed_event_teams)

        event_team = EventTeam.get_by_id("2011ct_frc177")
        self.assertEqual(event_team.year, 2011)
