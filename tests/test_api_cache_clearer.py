import json
import unittest2
import webtest
import webapp2

from datetime import datetime

from google.appengine.api import memcache
from google.appengine.ext import testbed

import api_main

from consts.award_type import AwardType
from consts.event_type import EventType
from consts.media_type import MediaType

from controllers.api.api_event_controller import ApiEventController
from controllers.api.api_event_controller import ApiEventListController
from controllers.api.api_event_controller import ApiEventTeamsController
from controllers.api.api_event_controller import ApiEventMatchesController
from controllers.api.api_event_controller import ApiEventStatsController
from controllers.api.api_event_controller import ApiEventRankingsController
from controllers.api.api_event_controller import ApiEventAwardsController

from controllers.api.api_team_controller import ApiTeamController
from controllers.api.api_team_controller import ApiTeamMediaController

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.media_manipulator import MediaManipulator
from helpers.team_manipulator import TeamManipulator

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
from models.team import Team


class TestApiCacheClearer(unittest2.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(api_main.app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        # populate mini db
        self.event_2010sc_1 = Event(
            id='2010sc',
            name='Palmetto Regional',
            event_type_enum=EventType.REGIONAL,
            short_name='Palmetto',
            event_short='sc',
            year=2010,
            end_date=datetime(2010, 03, 27),
            official=True,
            location='Clemson, SC',
            start_date=datetime(2010, 03, 24),
        )

        self.event_2010sc_2 = Event(
            id='2010sc',
            name='New Regional',
            event_type_enum=EventType.REGIONAL,
            short_name='Palmetto',
            event_short='sc',
            year=2010,
            end_date=datetime(2010, 03, 27),
            official=True,
            location='Clemson, SC',
            start_date=datetime(2010, 03, 24),
        )

        self.team_frc1_1 = Team(
            id='frc1',
            name='This is a name',
            team_number=1,
            nickname='NICKNAME',
            address='San Jose, CA, USA',
            website='www.usfirst.org',
        )

        self.team_frc1_2 = Team(
            id='frc1',
            name='This is a name',
            team_number=1,
            nickname='NICKNAME',
            address='San Jose, CA, USA',
            website='www.thebluealliance.com',
        )

        self.team_frc2_1 = Team(
            id='frc2',
            name='This is a name',
            team_number=2,
            nickname='NICKNAME',
            address='San Jose, CA, USA',
            website='www.usfirst.org',
        )

        self.team_frc2_2 = Team(
            id='frc2',
            name='This is a name',
            team_number=2,
            nickname='nickname',
            address='San Jose, CA, USA',
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
            game='frc_unknown',
            team_key_names=[u'frc1', u'frc2', u'frc3', u'frc4', u'frc5', u'frc6'],
        )

        self.match1_2 = Match(
            id='2010sc_qm1',
            alliances_json=json.dumps({'blue': {'score': -1, 'teams': ['frc1', 'frc999', 'frc3']}, 'red': {'score': -1, 'teams': ['frc4', 'frc5', 'frc6']}}),
            comp_level='qm',
            event=self.event_2010sc_1.key,
            set_number=1,
            match_number=1,
            game='frc_unknown',
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

        self.eventlist_2010_cache_key = ApiEventListController._get_full_cache_key(ApiEventListController.CACHE_KEY_FORMAT.format('2010'))
        self.event_2010sc_cache_key = ApiEventController._get_full_cache_key(ApiEventController.CACHE_KEY_FORMAT.format('2010sc'))
        self.eventteams_2010sc_cache_key = ApiEventTeamsController._get_full_cache_key(ApiEventTeamsController.CACHE_KEY_FORMAT.format('2010sc'))
        self.eventmatches_2010sc_cache_key = ApiEventMatchesController._get_full_cache_key(ApiEventMatchesController.CACHE_KEY_FORMAT.format('2010sc'))
        self.eventstats_2010sc_cache_key = ApiEventStatsController._get_full_cache_key(ApiEventStatsController.CACHE_KEY_FORMAT.format('2010sc'))
        self.eventrankings_2010sc_cache_key = ApiEventRankingsController._get_full_cache_key(ApiEventRankingsController.CACHE_KEY_FORMAT.format('2010sc'))
        self.eventawards_2010sc_cache_key = ApiEventAwardsController._get_full_cache_key(ApiEventAwardsController.CACHE_KEY_FORMAT.format('2010sc'))
        self.team_frc1_cache_key = ApiTeamController._get_full_cache_key(ApiTeamController.CACHE_KEY_FORMAT.format('frc1', 2010))
        self.team_frc2_cache_key = ApiTeamController._get_full_cache_key(ApiTeamController.CACHE_KEY_FORMAT.format('frc2', 2010))
        self.team_media_frc1_cache_key = ApiTeamMediaController._get_full_cache_key(ApiTeamMediaController.CACHE_KEY_FORMAT.format('frc1', 2010))
        self.team_media_frc2_cache_key = ApiTeamMediaController._get_full_cache_key(ApiTeamMediaController.CACHE_KEY_FORMAT.format('frc2', 2010))

    def tearDown(self):
        self.testbed.deactivate()

    def resetAll(self, flushed=False):
        response = self.testapp.get('/api/v2/events/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)

        EventManipulator.createOrUpdate(self.event_2010sc_1)
        if flushed:
            self.assertEqual(memcache.get(self.eventlist_2010_cache_key), None)
        TeamManipulator.createOrUpdate(self.team_frc1_1)
        TeamManipulator.createOrUpdate(self.team_frc2_1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc2)
        MatchManipulator.createOrUpdate(self.match1_1)
        AwardManipulator.createOrUpdate(self.award1_1)
        MediaManipulator.createOrUpdate(self.media1_1)

        response = self.testapp.get('/api/v2/events/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.event_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/teams', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/matches', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/stats', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/rankings', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/event/2010sc/awards', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/2010', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc1/2010/media', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        if flushed:
            self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        response = self.testapp.get('/api/v2/team/frc2/2010/media', headers={'X-TBA-App-Id': 'tba-tests:api-cache-clear-test:v01'})
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

    def testApiCacheClear(self):
        self.assertEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll(flushed=True)

        # this shouldn't evict any caches
        EventManipulator.createOrUpdate(self.event_2010sc_1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc1)
        EventTeamManipulator.createOrUpdate(self.eventteam_2010sc_frc2)
        AwardManipulator.createOrUpdate(self.award1_1)
        MatchManipulator.createOrUpdate(self.match1_1)
        TeamManipulator.createOrUpdate(self.team_frc1_1)
        TeamManipulator.createOrUpdate(self.team_frc2_1)
        MediaManipulator.createOrUpdate(self.media1_1)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        # updating an event
        EventManipulator.createOrUpdate(self.event_2010sc_2)
        self.assertEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # updating a team
        TeamManipulator.createOrUpdate(self.team_frc1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # updating a match
        MatchManipulator.createOrUpdate(self.match1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # updating an award
        AwardManipulator.createOrUpdate(self.award1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # updating a media
        MediaManipulator.createOrUpdate(self.media1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # deleting a media
        MediaManipulator.delete(self.media1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # deleting an award
        AwardManipulator.delete(self.award1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # deleting a match
        MatchManipulator.delete(self.match1_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # deleting a team
        TeamManipulator.delete(self.team_frc2_2)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # deleting an event
        EventManipulator.delete(self.event_2010sc_2)
        self.assertEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)

        self.resetAll()

        # deleting an eventteam
        EventTeamManipulator.delete(self.eventteam_2010sc_frc1)
        self.assertNotEqual(memcache.get(self.eventlist_2010_cache_key), None)
        self.assertNotEqual(memcache.get(self.event_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.eventteams_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventmatches_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventstats_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventrankings_2010sc_cache_key), None)
        self.assertNotEqual(memcache.get(self.eventawards_2010sc_cache_key), None)
        self.assertEqual(memcache.get(self.team_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_frc2_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc1_cache_key), None)
        self.assertNotEqual(memcache.get(self.team_media_frc2_cache_key), None)
