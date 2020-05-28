import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from database import get_affected_queries
from database.award_query import EventAwardsQuery, TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery, TeamEventTypeAwardsQuery
from database.district_query import DistrictsInYearQuery, DistrictHistoryQuery, DistrictQuery
from database.event_query import EventQuery, EventListQuery, DistrictEventsQuery, TeamEventsQuery, TeamYearEventsQuery, TeamYearEventTeamsQuery, \
    EventDivisionsQuery
from database.event_details_query import EventDetailsQuery
from database.gdcv_data_query import MatchGdcvDataQuery, EventMatchesGdcvDataQuery
from database.match_query import MatchQuery, EventMatchesQuery, TeamEventMatchesQuery, TeamYearMatchesQuery
from database.media_query import TeamSocialMediaQuery, TeamYearMediaQuery, EventTeamsMediasQuery, EventTeamsPreferredMediasQuery, \
    EventMediasQuery, TeamTagMediasQuery, TeamYearTagMediasQuery
from database.robot_query import TeamRobotsQuery
from database.team_query import TeamQuery, TeamListQuery, TeamListYearQuery, DistrictTeamsQuery, EventTeamsQuery, EventEventTeamsQuery, TeamParticipationQuery, TeamDistrictsQuery

from consts.event_type import EventType
from consts.award_type import AwardType
from consts.media_tag import MediaTag
from models.district import District
from models.district_team import DistrictTeam
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
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

        self.eventteam_2016necmp_frc125 = EventTeam(
            id='2016necmp_frc125',
            event=ndb.Key(Event, '2016necmp'),
            team=ndb.Key(Team, 'frc125'),
            year=2016,
        )

        self.eventteam_2015casj_frc254.put()
        self.eventteam_2015cama_frc604.put()
        self.eventteam_2010cama_frc604.put()
        self.eventteam_2016necmp_frc125.put()

        self.districtteam_2015fim_frc254 = DistrictTeam(
            id='2015fim_frc254',
            district_key=ndb.Key(District, '2015fim'),
            team=ndb.Key(Team, 'frc254'),
            year=2015,
        )

        self.districtteam_2015mar_frc604 = DistrictTeam(
            id='2015mar_frc604',
            district_key=ndb.Key(District, '2015mar'),
            team=ndb.Key(Team, 'frc604'),
            year=2015,
        )

        self.districtteam_2016ne_frc604 = DistrictTeam(
            id='2016ne_frc604',
            district_key=ndb.Key(District, '2016ne'),
            team=ndb.Key(Team, 'frc604'),
            year=2016,
        )

        self.districtteam_2015fim_frc254.put()
        self.districtteam_2015mar_frc604.put()
        self.districtteam_2016ne_frc604.put()

        self.district_2015ne = District(
            id='2015ne',
            year=2015,
            abbreviation='ne',
        )

        self.district_2016chs = District(
            id='2016chs',
            year=2016,
            abbreviation='chs',
        )
        self.district_2015ne.put()
        self.district_2016chs.put()

        self.event_2016necmp = Event(
            id='2016necmp',
            year=2016,
            district_key=ndb.Key(District, '2016ne'),
            event_short='necmp',
            event_type_enum=EventType.DISTRICT_CMP,
        )
        self.event_2016necmp.put()

        self.event_2015casj = Event(
            id='2015casj',
            year=2015,
            event_short='casj',
            event_type_enum=EventType.REGIONAL,
            parent_event=ndb.Key(Event, '2015cafoo'),
        )
        self.event_2015casj.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_award_updated(self):
        affected_refs = {
            'event': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'team_list': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015},
            'event_type_enum': {EventType.REGIONAL, EventType.DISTRICT},
            'award_type_enum': {AwardType.WINNER, AwardType.CHAIRMANS},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.award_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 20)
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
        for team_key in ['frc254', 'frc604']:
            for event_type in [EventType.REGIONAL, EventType.DISTRICT]:
                for award_type in [AwardType.WINNER, AwardType.CHAIRMANS]:
                    self.assertTrue(TeamEventTypeAwardsQuery(team_key, event_type, award_type).cache_key in cache_keys)

    def test_event_updated(self):
        affected_refs = {
            'key': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'year': {2014, 2015},
            'district_key': {ndb.Key(District, '2015fim'), ndb.Key(District, '2014mar')}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.event_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 15)
        self.assertTrue(EventQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventListQuery(2014).cache_key in cache_keys)
        self.assertTrue(EventListQuery(2015).cache_key in cache_keys)
        self.assertTrue(DistrictEventsQuery('2015fim').cache_key in cache_keys)
        self.assertTrue(DistrictEventsQuery('2014mar').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(EventDivisionsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventDivisionsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventDivisionsQuery('2015cafoo').cache_key in cache_keys)

    def test_event_details_updated(self):
        affected_refs = {
            'key': {ndb.Key(EventDetails, '2015casj'), ndb.Key(EventDetails, '2015cama')},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.event_details_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 2)
        self.assertTrue(EventDetailsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventDetailsQuery('2015cama').cache_key in cache_keys)

    def test_match_updated(self):
        affected_refs = {
            'key': {ndb.Key(Match, '2015casj_qm1'), ndb.Key(Match, '2015casj_qm2')},
            'event': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'team_keys': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.match_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 16)
        self.assertTrue(MatchQuery('2015casj_qm1').cache_key in cache_keys)
        self.assertTrue(MatchQuery('2015casj_qm2').cache_key in cache_keys)
        self.assertTrue(MatchGdcvDataQuery('2015casj_qm1').cache_key in cache_keys)
        self.assertTrue(MatchGdcvDataQuery('2015casj_qm2').cache_key in cache_keys)
        self.assertTrue(EventMatchesQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventMatchesQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventMatchesGdcvDataQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventMatchesGdcvDataQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc254', '2015casj').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc254', '2015cama').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc604', '2015casj').cache_key in cache_keys)
        self.assertTrue(TeamEventMatchesQuery('frc604', '2015cama').cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearMatchesQuery('frc604', 2015).cache_key in cache_keys)

    def test_media_updated_team(self):
        affected_refs = {
            'references': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015},
            'media_tag_enum': {MediaTag.CHAIRMANS_ESSAY, MediaTag.CHAIRMANS_VIDEO},
        }
        cache_keys = [q.cache_key for q in get_affected_queries.media_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 22)
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
        self.assertTrue(TeamTagMediasQuery('frc254', MediaTag.CHAIRMANS_ESSAY).cache_key in cache_keys)
        self.assertTrue(TeamTagMediasQuery('frc604', MediaTag.CHAIRMANS_VIDEO).cache_key in cache_keys)
        self.assertTrue(TeamYearTagMediasQuery('frc254', MediaTag.CHAIRMANS_ESSAY, 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearTagMediasQuery('frc604', MediaTag.CHAIRMANS_VIDEO, 2015).cache_key in cache_keys)

    def test_media_updated_event(self):
        affected_refs = {
            'references': {ndb.Key(Event, '2016necmp')},
            'year': {2016},
            'media_tag_enum': {None, None}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.media_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 1)
        self.assertTrue(EventMediasQuery('2016necmp').cache_key in cache_keys)

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

        self.assertEqual(len(cache_keys), 16)
        self.assertTrue(TeamQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamListQuery(0).cache_key in cache_keys)
        self.assertTrue(TeamListQuery(1).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 0).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 1).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2010, 1).cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2015fim').cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2015mar').cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2016ne').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2010cama').cache_key in cache_keys)
        self.assertTrue(EventEventTeamsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventEventTeamsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventEventTeamsQuery('2010cama').cache_key in cache_keys)

    def test_eventteam_updated(self):
        affected_refs = {
            'event': {ndb.Key(Event, '2015casj'), ndb.Key(Event, '2015cama')},
            'team': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')},
            'year': {2014, 2015}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.eventteam_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 24)
        self.assertTrue(TeamEventsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamParticipationQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamParticipationQuery('frc604').cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc254', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc254', 2015).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc604', 2014).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc604', 2015).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2014, 0).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2014, 1).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 0).cache_key in cache_keys)
        self.assertTrue(TeamListYearQuery(2015, 1).cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventEventTeamsQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventEventTeamsQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsMediasQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsMediasQuery('2015casj').cache_key in cache_keys)
        self.assertTrue(EventTeamsPreferredMediasQuery('2015cama').cache_key in cache_keys)
        self.assertTrue(EventTeamsPreferredMediasQuery('2015casj').cache_key in cache_keys)

    def test_districtteam_updated(self):
        affected_refs = {
            'district_key': {ndb.Key(District, '2015fim'), ndb.Key(District, '2015mar')},
            'team': {ndb.Key(Team, 'frc254'), ndb.Key(Team, 'frc604')}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.districtteam_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 4)
        self.assertTrue(DistrictTeamsQuery('2015fim').cache_key in cache_keys)
        self.assertTrue(DistrictTeamsQuery('2015mar').cache_key in cache_keys)
        self.assertTrue(TeamDistrictsQuery('frc254').cache_key in cache_keys)
        self.assertTrue(TeamDistrictsQuery('frc604').cache_key in cache_keys)

    def test_district_updated(self):
        affected_refs = {
            'key': {ndb.Key(District, '2016ne')},
            'year': {2015, 2016},
            'abbreviation': {'ne', 'chs'}
        }
        cache_keys = [q.cache_key for q in get_affected_queries.district_updated(affected_refs)]

        self.assertEqual(len(cache_keys), 13)
        self.assertTrue(DistrictsInYearQuery(2015).cache_key in cache_keys)
        self.assertTrue(DistrictsInYearQuery(2016).cache_key in cache_keys)
        self.assertTrue(DistrictHistoryQuery('ne').cache_key in cache_keys)
        self.assertTrue(DistrictHistoryQuery('chs').cache_key in cache_keys)
        self.assertTrue(DistrictQuery('2016ne').cache_key in cache_keys)
        self.assertTrue(TeamDistrictsQuery('frc604').cache_key in cache_keys)

        # Necessary because APIv3 Event models include the District model
        self.assertTrue(EventQuery('2016necmp').cache_key in cache_keys)
        self.assertTrue(EventListQuery(2016).cache_key in cache_keys)
        self.assertTrue(DistrictEventsQuery('2016ne').cache_key in cache_keys)
        self.assertTrue(TeamEventsQuery('frc125').cache_key in cache_keys)
        self.assertTrue(TeamYearEventsQuery('frc125', 2016).cache_key in cache_keys)
        self.assertTrue(TeamYearEventTeamsQuery('frc125', 2016).cache_key in cache_keys)
        self.assertTrue(EventDivisionsQuery('2016necmp').cache_key in cache_keys)
