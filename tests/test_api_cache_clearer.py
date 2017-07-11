import json
import unittest2
import webtest

from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.api import taskqueue
from google.appengine.ext import testbed

import api_main
import tba_config
from consts.award_type import AwardType
from consts.event_type import EventType
from consts.media_type import MediaType

from controllers.api.api_district_controller import ApiDistrictListController
from controllers.api.api_district_controller import ApiDistrictEventsController
from controllers.api.api_district_controller import ApiDistrictRankingsController

from controllers.api.api_event_controller import ApiEventController
from controllers.api.api_event_controller import ApiEventListController
from controllers.api.api_event_controller import ApiEventTeamsController
from controllers.api.api_event_controller import ApiEventMatchesController
from controllers.api.api_event_controller import ApiEventStatsController
from controllers.api.api_event_controller import ApiEventRankingsController
from controllers.api.api_event_controller import ApiEventAwardsController
from controllers.api.api_event_controller import ApiEventDistrictPointsController

from controllers.api.api_match_controller import ApiMatchController

from controllers.api.api_team_controller import ApiTeamController
from controllers.api.api_team_controller import ApiTeamEventsController
from controllers.api.api_team_controller import ApiTeamEventAwardsController
from controllers.api.api_team_controller import ApiTeamEventMatchesController
from controllers.api.api_team_controller import ApiTeamMediaController
from controllers.api.api_team_controller import ApiTeamYearsParticipatedController
from controllers.api.api_team_controller import ApiTeamListController
from controllers.api.api_team_controller import ApiTeamHistoryRobotsController

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.media_manipulator import MediaManipulator
from helpers.robot_manipulator import RobotManipulator
from helpers.team_manipulator import TeamManipulator

from models.award import Award
from models.cached_response import CachedResponse
from models.district import District
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
from models.robot import Robot
from models.team import Team


class TestApiCacheClearer(unittest2.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(api_main.app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        # Enable the cache we're testing
        tba_config.CONFIG['response_cache'] = True

        self.district_2010fim = District(
            id='2010fim',
            year=2010,
            abbreviation='fim',
        )
        self.district_2010fim.put()

        # populate mini db
        self.event_2010sc_1 = Event(
            id='2010sc',
            name='Palmetto Regional',
            event_type_enum=EventType.REGIONAL,
            district_key=ndb.Key(District, '2010fim'),
            short_name='Palmetto',
            event_short='sc',
            year=2010,
            end_date=datetime(2010, 03, 27),
            official=True,
            city="Clemson",
            state_prov="SC",
            country="USA",
            start_date=datetime(2010, 03, 24),
        )

        self.event_2010sc_2 = Event(
            id='2010sc',
            name='New Regional',
            event_type_enum=EventType.REGIONAL,
            district_key=ndb.Key(District, '2010fim'),
            short_name='Palmetto',
            event_short='sc',
            year=2010,
            end_date=datetime(2010, 03, 27),
            official=True,
            city="Clemson",
            state_prov="SC",
            country="USA",
            start_date=datetime(2010, 03, 24),
        )

        self.team_frc1_1 = Team(
            id='frc1',
            name='This is a name',
            team_number=1,
            nickname='NICKNAME',
            city='San Jose',
            state_prov='CA',
            country='USA',
            website='www.usfirst.org',
        )

        self.team_frc1_2 = Team(
            id='frc1',
            name='This is a name',
            team_number=1,
            nickname='NICKNAME',
            city='San Jose',
            state_prov='CA',
            country='USA',
            website='www.thebluealliance.com',
        )

        self.team_frc2_1 = Team(
            id='frc2',
            name='This is a name',
            team_number=2,
            nickname='NICKNAME',
            city='San Jose',
            state_prov='CA',
            country='USA',
            website='www.usfirst.org',
        )

        self.team_frc2_2 = Team(
            id='frc2',
            name='This is a name',
            team_number=2,
            nickname='nickname',
            city='San Jose',
            state_prov='CA',
            country='USA',
            website='www.usfirst.org',
        )

        self.eventteam_2010sc_frc1 = EventTeam(
            id='2010sc_frc1',
            event=self.event_2010sc_1.key,
            team=self.team_frc1_1.key,
            year=2010,
        )

        self.eventteam_2010sc_frc2 = EventTeam(
            id='2010sc_frc2',
            event=self.event_2010sc_1.key,
            team=self.team_frc2_1.key,
            year=2010,
        )

        self.match1_1 = Match(
            id='2010sc_qm1',
            alliances_json=json.dumps({'blue': {'score': -1, 'teams': ['frc1', 'frc2', 'frc3']}, 'red': {'score': -1, 'teams': ['frc4', 'frc5', 'frc6']}}),
            comp_level='qm',
            event=self.event_2010sc_1.key,
            set_number=1,
            match_number=1,
            year=2010,
            team_key_names=[u'frc1', u'frc2', u'frc3', u'frc4', u'frc5', u'frc6'],
        )

        self.match1_2 = Match(
            id='2010sc_qm1',
            alliances_json=json.dumps({'blue': {'score': -1, 'teams': ['frc1', 'frc999', 'frc3']}, 'red': {'score': -1, 'teams': ['frc4', 'frc5', 'frc6']}}),
            comp_level='qm',
            event=self.event_2010sc_1.key,
            set_number=1,
            match_number=1,
            year=2010,
            team_key_names=[u'frc1', u'frc999', u'frc3', u'frc4', u'frc5', u'frc6'],
        )

        self.award1_1 = Award(
            id="2010sc_1",
            name_str="Regional Champion",
            award_type_enum=AwardType.WINNER,
            year=2010,
            event=self.event_2010sc_1.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[self.team_frc1_1.key],
            recipient_json_list=[json.dumps({'team_number': 1, 'awardee': None})],
        )

        self.award1_2 = Award(
            id="2010sc_1",
            name_str="Regional Champion",
            award_type_enum=AwardType.WINNER,
            year=2010,
            event=self.event_2010sc_1.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[self.team_frc2_1.key],
            recipient_json_list=[json.dumps({'team_number': 2, 'awardee': None})],
        )

        self.media1_1 = Media(
            id='cdphotothread_39894',
            media_type_enum=MediaType.CD_PHOTO_THREAD,
            foreign_key='39894',
            details_json='{"image_partial": "fe3/fe38d320428adf4f51ac969efb3db32c_l.jpg"}',
            year=2010,
            references=[self.team_frc1_1.key],
        )

        self.media1_2 = Media(
            id='cdphotothread_39894',
            media_type_enum=MediaType.CD_PHOTO_THREAD,
            foreign_key='39894',
            details_json='{"image_partial": "fe3/fe38d320428adf4f51ac969efb3db32c_l.jpg"}',
            year=2010,
            references=[self.team_frc2_1.key],
        )

        self.districtlist_2010_cache_key = ApiDistrictListController.get_cache_key_from_format('2010')
        self.district_events_2010_cache_key = ApiDistrictEventsController.get_cache_key_from_format('fim', '2010')
        self.district_rankings_2010_cache_key = ApiDistrictRankingsController.get_cache_key_from_format('fim', '2010')

        self.eventlist_2010_cache_key = ApiEventListController.get_cache_key_from_format('2010')
        self.event_2010sc_cache_key = ApiEventController.get_cache_key_from_format('2010sc')
        self.eventteams_2010sc_cache_key = ApiEventTeamsController.get_cache_key_from_format('2010sc')
        self.eventmatches_2010sc_cache_key = ApiEventMatchesController.get_cache_key_from_format('2010sc')
        self.eventstats_2010sc_cache_key = ApiEventStatsController.get_cache_key_from_format('2010sc')
        self.eventrankings_2010sc_cache_key = ApiEventRankingsController.get_cache_key_from_format('2010sc')
        self.eventawards_2010sc_cache_key = ApiEventAwardsController.get_cache_key_from_format('2010sc')
        self.eventdistrictpoints_2010sc_cache_key = ApiEventDistrictPointsController.get_cache_key_from_format('2010sc')

        self.match_cache_key = ApiMatchController.get_cache_key_from_format('2010sc_qm1')

        self.team_frc1_cache_key = ApiTeamController.get_cache_key_from_format('frc1', 2010)
        self.team_frc2_cache_key = ApiTeamController.get_cache_key_from_format('frc2', 2010)

        self.team_events_frc1_cache_key = ApiTeamEventsController.get_cache_key_from_format('frc1', 2010)
        self.team_events_frc2_cache_key = ApiTeamEventsController.get_cache_key_from_format('frc2', 2010)

        self.team_event_awards_frc1_2010sc_cache_key = ApiTeamEventAwardsController.get_cache_key_from_format('frc1', '2010sc')
        self.team_event_awards_frc2_2010sc_cache_key = ApiTeamEventAwardsController.get_cache_key_from_format('frc2', '2010sc')
        self.team_event_matches_frc1_2010sc_cache_key = ApiTeamEventMatchesController.get_cache_key_from_format('frc1', '2010sc')
        self.team_event_matches_frc2_2010sc_cache_key = ApiTeamEventMatchesController.get_cache_key_from_format('frc2', '2010sc')

        self.team_media_frc1_cache_key = ApiTeamMediaController.get_cache_key_from_format('frc1', 2010)
        self.team_media_frc2_cache_key = ApiTeamMediaController.get_cache_key_from_format('frc2', 2010)

        self.team_years_participated_frc1_cache_key = ApiTeamYearsParticipatedController.get_cache_key_from_format('frc1')
        self.team_years_participated_frc2_cache_key = ApiTeamYearsParticipatedController.get_cache_key_from_format('frc2')

        self.team_list_page_0_cache_key = ApiTeamListController.get_cache_key_from_format(0)
        self.team_list_page_1_cache_key = ApiTeamListController.get_cache_key_from_format(1)

        self.robot1 = Robot(
            id='frc1_2015',
            year=2015,
            team=self.team_frc1_1.key,
            robot_name='Baymax'
        )
        self.robot2 = Robot(
            id='frc1_2015',
            year=2015,
            team=self.team_frc1_1.key,
            robot_name='Wall-E'
        )
        self.robots_cache_key = ApiTeamHistoryRobotsController.get_cache_key_from_format('frc1')

    def tearDown(self):
        self.testbed.deactivate()

    def processDeferred(self):
        """
        Cache clearing is done in a deferred task. Force it to run here.
        """
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='cache-clearing')
        queue = taskqueue.Queue('cache-clearing')
        for task in tasks:
            deferred.run(task.payload)
            queue.delete_tasks(task)

    def test_robots(self):
        self.assertEqual(CachedResponse.get_by_id(self.robots_cache_key), None)
        TeamManipulator.createOrUpdate(self.team_frc1_1)
        RobotManipulator.createOrUpdate(self.robot1)
        self.processDeferred()
        response = self.testapp.get('/api/v2/team/frc1/history/robots', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.robots_cache_key), None)

        RobotManipulator.createOrUpdate(self.robot2)
        self.processDeferred()

        self.assertEqual(CachedResponse.get_by_id(self.robots_cache_key), None)
        response = self.testapp.get('/api/v2/team/frc1/history/robots', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.robots_cache_key), None)

    def test_reset_all(self, flushed=False):
        response = self.testapp.get('/api/v2/events/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)

        EventManipulator.createOrUpdate(self.event_2010sc_1)
        self.processDeferred()
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        TeamManipulator.createOrUpdate(self.team_frc1_1)
        TeamManipulator.createOrUpdate(self.team_frc2_1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc2)
        MatchManipulator.createOrUpdate(self.match1_1)
        AwardManipulator.createOrUpdate(self.award1_1)
        MediaManipulator.createOrUpdate(self.media1_1)
        self.processDeferred()

        response = self.testapp.get('/api/v2/events/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/teams', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/matches', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/stats', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/rankings', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/awards', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/district_points', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/match/2010sc_qm1', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/2010/events', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/2010/events', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/event/2010sc/awards', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/event/2010sc/awards', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/event/2010sc/matches', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/event/2010sc/matches', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/2010/media', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/2010/media', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/years_participated', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/years_participated', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/teams/0', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/teams/1', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/districts/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/district/fim/2010/events', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        if flushed:
            self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        response = self.testapp.get('/api/v2/district/fim/2010/rankings', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

    def testApiCacheClear(self):
        self.assertEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all(flushed=True)

        # this shouldn't evict any caches
        EventManipulator.createOrUpdate(self.event_2010sc_1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc2)
        AwardManipulator.createOrUpdate(self.award1_1)
        MatchManipulator.createOrUpdate(self.match1_1)
        TeamManipulator.createOrUpdate(self.team_frc1_1)
        TeamManipulator.createOrUpdate(self.team_frc2_1)
        MediaManipulator.createOrUpdate(self.media1_1)
        self.processDeferred()

        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        # updating an event
        EventManipulator.createOrUpdate(self.event_2010sc_2)
        self.processDeferred()
        self.assertEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # updating a team
        TeamManipulator.createOrUpdate(self.team_frc1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # updating a match
        MatchManipulator.createOrUpdate(self.match1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # updating an award
        AwardManipulator.createOrUpdate(self.award1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # updating a media
        MediaManipulator.createOrUpdate(self.media1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # deleting a media
        MediaManipulator.delete(self.media1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # deleting an award
        AwardManipulator.delete(self.award1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # deleting a match
        MatchManipulator.delete(self.match1_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # deleting a team
        TeamManipulator.delete(self.team_frc2_2)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # deleting an event
        EventManipulator.delete(self.event_2010sc_2)
        self.processDeferred()
        self.assertEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)

        self.test_reset_all()

        # deleting an eventteam
        EventTeamManipulator.delete(self.eventteam_2010sc_frc1)
        self.processDeferred()
        self.assertNotEqual(CachedResponse.get_by_id(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.event_2010sc_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.eventdistrictpoints_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.match_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_events_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_events_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_awards_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc1_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_event_matches_frc2_2010sc_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_media_frc2_cache_key), None)
        self.assertEqual(CachedResponse.get_by_id(self.team_years_participated_frc1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_years_participated_frc2_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_0_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.team_list_page_1_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.districtlist_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_events_2010_cache_key), None)
        self.assertNotEqual(CachedResponse.get_by_id(self.district_rankings_2010_cache_key), None)
