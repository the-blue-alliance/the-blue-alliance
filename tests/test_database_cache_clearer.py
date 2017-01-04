import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from database import get_affected_queries
from database.award_query import EventAwardsQuery, TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery
from database.event_query import EventListQuery, DistrictEventsQuery, TeamEventsQuery, TeamYearEventsQuery
from database.match_query import EventMatchesQuery, TeamEventMatchesQuery, TeamYearMatchesQuery
from database.media_query import TeamSocialMediaQuery, TeamYearMediaQuery, EventTeamsMediasQuery, EventTeamsPreferredMediasQuery
from database.robot_query import TeamRobotsQuery
from database.team_query import TeamQuery, TeamListQuery, TeamListYearQuery, DistrictTeamsQuery, EventTeamsQuery, TeamParticipationQuery, TeamDistrictsQuery

from consts.district_type import DistrictType

from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class TestDatabaseCacheClearer(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.eventteam_2015casj_frc254 = EventTeam(
            id='2015casj_frc254',
            event=ndb.Key(Event, '2015casj'),
            team=ndb.Key(Team, 'frc254'),
            year=2015,
        )

        self.eventteam_2015cama_frc604 = EventTeam(
            id='2015cama_frc604',
            event=ndb.Key(Event, '2015cama'),
            team=ndb.Key(Team, 'frc604'),
            year=2015,
        )

        self.eventteam_2010cama_frc604 = EventTeam(
            id='2010cama_frc604',
            event=ndb.Key(Event, '2010cama'),
            team=ndb.Key(Team, 'frc604'),
            year=2010,
        )

        self.eventteam_2015casj_frc254.put()
        self.eventteam_2015cama_frc604.put()
        self.eventteam_2010cama_frc604.put()

        self.districtteam_2015fim_frc254 = DistrictTeam(
            id='2015fim_frc254',
            district=DistrictType.MICHIGAN,
            team=ndb.Key(Team, 'frc254'),
            year=2015,
        )

        self.districtteam_2015mar_frc604 = DistrictTeam(
            id='2015mar_frc604',
            district=DistrictType.MID_ATLANTIC,
            team=ndb.Key(Team, 'frc604'),
            year=2015,
        )

        self.districtteam_2015fim_frc254.put()
        self.districtteam_2015mar_frc604.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_award_updated(self):
        affected_refs = {
            'event': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'team_list': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.award_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 12)
        self.assertTrue(EventAwardsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventAwardsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(TeamAwardsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamAwardsQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamYearAwardsQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearAwardsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearAwardsQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearAwardsQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(TeamEventAwardsQuery('frc254', '2015casj').cache_key in cache_keys)
        self.assertTrue(TeamEventAwardsQuery('frc254', '2015cama').cache_key in cache_keys)
        self.assertTrue(TeamEventAwardsQuery('frc604', '2015casj').cache_key in cache_keys)
        self.assertTrue(TeamEventAwardsQuery('frc604', '2015cama').cache_key in cache_keys)

    def test_event_updated(self):
        affected_refs = {
            'key': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'year': {2014, 2015},
            'event_district_key': {'2015fim', '2014mar'}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.event_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 8)
        self.assertTrue(EventListQuery(2014).cache_key in cache_keys)
        self.assertTrue(EventListQuery(2015).cache_key in cache_keys)
        self.assertTrue(DistrictEventsQuery('2015fim').cache_key in cache_keys)
        self.assertTrue(DistrictEventsQuery('2014mar').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc604', 2015).cache_key in cache_keys)

    def test_match_updated(self):
        affected_refs = {
            'event': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'team_keys': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.match_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 10)
        self.assertTrue(EventMatchesQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventMatchesQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc254', '2015casj').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc254', '2015cama').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc604', '2015casj').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc604', '2015cama').cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc604', 2015).cache_key in cache_keys)

    def test_media_updated(self):
        affected_refs = {
            'references': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.media_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 10)
        self.assertTrue(TeamYearMediaQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearMediaQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamSocialMediaQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamYearMediaQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearMediaQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(TeamSocialMediaQuery('frc604').cache_key in cache_keys)
        self.assertTrue(EventTeamsMediasQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsMediasQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsPreferredMediasQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsPreferredMediasQuery('2015casj').cache_key in cache_keys)

    def test_robot_updated(self):
        affected_refs = {
            'team': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.robot_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 2)
        self.assertTrue(TeamRobotsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamRobotsQuery('frc604').cache_key in cache_keys)

    def test_team_updated(self):
        affected_refs = {
            'key': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.team_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 12)
        self.assertTrue(TeamQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamListQuery(0).cache_key in cache_keys)
        self.assertTrue(TeamListQuery(1).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 0).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 1).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2010, 1).cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2015fim').cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2015mar').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2010cama').cache_key in cache_keys)

    def test_eventteam_updated(self):
        affected_refs = {
            'event': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'team': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.eventteam_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 18)
        self.assertTrue(TeamEventsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamParticipationQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamParticipationQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2014, 0).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2014, 1).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 0).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 1).cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsMediasQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsMediasQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsPreferredMediasQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsPreferredMediasQuery('2015casj').cache_key in cache_keys)

    def test_districtteam_updated(self):
        affected_refs = {
            'district_key': {'2015fim', '2015mar'},
            'team': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.districtteam_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 4)
        self.assertTrue(DistrictTeamsQuery('2015fim').cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2015mar').cache_key in cache_keys)
        self.assertTrue(TeamDistrictsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamDistrictsQuery('frc604').cache_key in cache_keys)
