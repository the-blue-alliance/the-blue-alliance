import datetime
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError, InvalidArgumentError, InternalError, UnavailableError
from firebase_admin.messaging import QuotaExceededError, SenderIdMismatchError, ThirdPartyAuthError, UnregisteredError
import json
from mock import patch, Mock, ANY
import unittest2

from google.appengine.api.taskqueue import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.award_type import AwardType
from consts.client_type import ClientType
from consts.event_type import EventType
from consts.model_type import ModelType
from consts.notification_type import NotificationType
import helpers.tbans_helper
from helpers.event.event_test_creator import EventTestCreator
from helpers.match.match_test_creator import MatchTestCreator
from helpers.tbans_helper import TBANSHelper, _firebase_app
from models.account import Account
from models.award import Award
from models.event import Event
from models.event_details import EventDetails
from models.match import Match
from models.team import Team
from models.mobile_client import MobileClient
from models.subscription import Subscription
from models.notifications.alliance_selection import AllianceSelectionNotification
from models.notifications.awards import AwardsNotification
from models.notifications.broadcast import BroadcastNotification
from models.notifications.event_level import EventLevelNotification
from models.notifications.event_schedule import EventScheduleNotification
from models.notifications.match_score import MatchScoreNotification
from models.notifications.match_upcoming import MatchUpcomingNotification
from models.notifications.match_video import MatchVideoNotification
from models.notifications.requests.fcm_request import FCMRequest
from models.notifications.requests.webhook_request import WebhookRequest

from tests.mocks.notifications.mock_notification import MockNotification


def fcm_messaging_ids(user_id):
    clients = MobileClient.query(
        MobileClient.client_type.IN(ClientType.FCM_CLIENTS),
        ancestor=ndb.Key(Account, user_id)
    ).fetch(projection=[MobileClient.messaging_id])
    return [c.messaging_id for c in clients]


class TestTBANSHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_app_identity_stub()
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests
        self.event = EventTestCreator.createFutureEvent()
        self.team = Team(
            id='frc7332',
            team_number=7332
        )
        self.team.put()
        self.match = Match(
            id='2020miket_qm1',
            event=self.event.key,
            comp_level='qm',
            set_number=1,
            match_number=1,
            team_key_names=['frc7332'],
            alliances_json=json.dumps({
                'red': {
                    'teams': ['frc1', 'frc2', 'frc7332'],
                    'score': -1,
                },
                'blue': {
                    'teams': ['frc4', 'frc5', 'frc6'],
                    'score': -1,
                }
            }),
            year=2020
        )

    def tearDown(self):
        self.testbed.deactivate()

    def test_firebase_app(self):
        # Make sure we can get an original Firebase app
        app_one = _firebase_app()
        self.assertIsNotNone(app_one)
        self.assertEqual(app_one.name, 'tbans')
        # Make sure duplicate calls don't crash
        app_two = _firebase_app()
        self.assertIsNotNone(app_two)
        self.assertEqual(app_two.name, 'tbans')
        # Should be the same object
        self.assertEqual(app_one, app_two)

    def test_alliance_selection_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.alliance_selection(self.event)
            mock_send.assert_not_called()

    def test_alliance_selection_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.alliance_selection(self.event, 'user_id')
            mock_send.assert_called_once()
            user_id = mock_send.call_args[0][0]
            self.assertEqual(user_id, ['user_id'])

    def test_alliance_selection(self):
        # Insert a Subscription for this Event and these Teams so we call to send
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='frc1',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.ALLIANCE_SELECTION]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.ALLIANCE_SELECTION]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_3'),
            user_id='user_id_3',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.ALLIANCE_SELECTION]
        ).put()

        # Insert EventDetails for the event with alliance selection information
        EventDetails(
            id=self.event.key_name,
            alliance_selections=[
                {"declines": [], "picks": ["frc7332"]}
            ]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.alliance_selection(self.event)
            # Two calls total - First to the Event, second to frc7332, no call for frc1
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 2)
            self.assertEqual([x[0] for x in [call[0][0] for call in mock_send.call_args_list]], ['user_id_3', 'user_id_2'])
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                self.assertTrue(isinstance(notification, AllianceSelectionNotification))
            # Check Event notification
            event_notification = notifications[0]
            self.assertEqual(event_notification.event, self.event)
            self.assertIsNone(event_notification.team)
            # Check frc7332 notification
            team_notification = notifications[1]
            self.assertEqual(team_notification.event, self.event)
            self.assertEqual(team_notification.team, self.team)

    def test_awards_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.awards(self.event)
            mock_send.assert_not_called()

    def test_awards_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.awards(self.event, 'user_id')
            mock_send.assert_called_once()
            user_id = mock_send.call_args[0][0]
            self.assertEqual(user_id, ['user_id'])

    def test_awards(self):
        # Insert some Awards for some Teams
        award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.INDUSTRIAL_DESIGN),
            name_str='Industrial Design Award sponsored by General Motors',
            award_type_enum=AwardType.INDUSTRIAL_DESIGN,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, 'frc7332')],
            year=2020
        )
        award.put()
        winner_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.WINNER),
            name_str='Regional Event Winner',
            award_type_enum=AwardType.WINNER,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, 'frc7332'), ndb.Key(Team, 'frc1')],
            year=2020
        )
        winner_award.put()
        frc_1 = Team(
            id='frc1',
            team_number=1
        )
        frc_1.put()

        # Insert a Subscription for this Event and these Teams so we call to send
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key='frc1',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.AWARDS]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.AWARDS]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_3'),
            user_id='user_id_3',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.AWARDS]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.awards(self.event)
            # Three calls total - First to the Event, second to frc7332 (two awards), third to frc1 (one award)
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            self.assertEqual([x[0] for x in [call[0][0] for call in mock_send.call_args_list]], ['user_id_3', 'user_id_1', 'user_id_2'])
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                self.assertTrue(isinstance(notification, AwardsNotification))
            # Check Event notification
            event_notification = notifications[0]
            self.assertEqual(event_notification.event, self.event)
            self.assertIsNone(event_notification.team)
            self.assertEqual(event_notification.team_awards, [])
            # Check frc1 notification
            event_notification = notifications[1]
            self.assertEqual(event_notification.event, self.event)
            self.assertEqual(event_notification.team, frc_1)
            self.assertEqual(len(event_notification.team_awards), 1)
            # Check frc7332 notification
            event_notification = notifications[2]
            self.assertEqual(event_notification.event, self.event)
            self.assertEqual(event_notification.team, self.team)
            self.assertEqual(len(event_notification.team_awards), 2)

    def test_broadcast_none(self):
        from notifications.base_notification import BaseNotification
        with patch.object(BaseNotification, 'send') as mock_send:
            TBANSHelper.broadcast([], 'Broadcast', 'Test broadcast')
            # Make sure we didn't send to Android
            mock_send.assert_not_called()

        # Make sure we didn't send to FCM or webhooks
        tasks = self.taskqueue_stub.GetTasks('push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_broadcast_fcm_empty(self):
        from notifications.base_notification import BaseNotification

        for client_type in ClientType.FCM_CLIENTS:
            with patch.object(BaseNotification, 'send') as mock_send:
                TBANSHelper.broadcast([client_type], 'Broadcast', 'Test broadcast')
                # Make sure we didn't send to Android
                mock_send.assert_not_called()

            # Make sure we didn't send to FCM or webhooks
            tasks = self.taskqueue_stub.GetTasks('push-notifications')
            self.assertEqual(len(tasks), 0)

    def test_broadcast_fcm(self):
        for client_type in ClientType.FCM_CLIENTS:
            client = MobileClient(
                parent=ndb.Key(Account, 'user_id'),
                user_id='user_id',
                messaging_id='token',
                client_type=client_type,
                device_uuid='uuid',
                display_name='Phone')
            client_key = client.put()

            from notifications.base_notification import BaseNotification
            with patch.object(BaseNotification, 'send') as mock_send:
                TBANSHelper.broadcast([client_type], 'Broadcast', 'Test broadcast')
                # Make sure we didn't send to Android
                mock_send.assert_not_called()

            # Make sure we'll send to FCM clients
            tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
            self.assertEqual(len(tasks), 1)

            # Make sure our taskqueue tasks execute what we expect
            with patch.object(TBANSHelper, '_send_fcm') as mock_send_fcm:
                deferred.run(tasks[0].payload)
                mock_send_fcm.assert_called_once_with([client], ANY)
                # Make sure the notification is a BroadcastNotification
                notification = mock_send_fcm.call_args[0][1]
                self.assertTrue(isinstance(notification, BroadcastNotification))

            self.taskqueue_stub.FlushQueue('push-notifications')

            client_key.delete()

    def test_broadcast_webhook_empty(self):
        from notifications.base_notification import BaseNotification

        with patch.object(BaseNotification, 'send') as mock_send:
            TBANSHelper.broadcast([ClientType.WEBHOOK], 'Broadcast', 'Test broadcast')
            # Make sure we didn't send to Android
            mock_send.assert_not_called()

        # Make sure we didn't send to FCM or webhooks
        tasks = self.taskqueue_stub.GetTasks('push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_broadcast_webhook(self):
        from notifications.base_notification import BaseNotification

        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.WEBHOOK,
            device_uuid='uuid',
            display_name='Phone')
        client_key = client.put()

        with patch.object(BaseNotification, 'send') as mock_send:
            TBANSHelper.broadcast([ClientType.WEBHOOK], 'Broadcast', 'Test broadcast')
            # Make sure we didn't send to Android
            mock_send.assert_not_called()

        # Make sure we'll send to FCM clients
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, '_send_webhook') as mock_send_webhook:
            deferred.run(tasks[0].payload)
            mock_send_webhook.assert_called_once_with([client], ANY)
            # Make sure the notification is a BroadcastNotification
            notification = mock_send_webhook.call_args[0][1]
            self.assertTrue(isinstance(notification, BroadcastNotification))

    def test_broadcast_android(self):
        client_type = ClientType.OS_ANDROID
        messaging_id = 'token'

        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id=messaging_id,
            client_type=client_type,
            device_uuid='uuid',
            display_name='Phone')
        client.put()

        from notifications.broadcast import BroadcastNotification
        with patch.object(BroadcastNotification, 'send') as mock_send:
            TBANSHelper.broadcast([client_type], 'Broadcast', 'Test broadcast')
            mock_send.assert_called_once_with({client_type: [messaging_id]})

        # Make sure we didn't send to FCM or webhooks
        tasks = self.taskqueue_stub.GetTasks('push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_event_level_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.event_level(self.match)
            mock_send.assert_not_called()

    def test_event_level_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.event_level(self.match, 'user_id')
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 1)
            for call in mock_send.call_args_list:
                self.assertEqual(call[0][0], ['user_id'])

    def test_event_level(self):
        # Insert a Subscription for this Event
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.LEVEL_STARTING]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.event_level(self.match)
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 1)
            user_ids = mock_send.call_args[0][0]
            self.assertEqual(user_ids, ['user_id_1'])
            notification = mock_send.call_args[0][1]
            self.assertTrue(isinstance(notification, EventLevelNotification))
            self.assertEqual(notification.match, self.match)
            self.assertEqual(notification.event, self.event)

    def test_event_schedule_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.event_schedule(self.event)
            mock_send.assert_not_called()

    def test_event_schedule_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.event_schedule(self.event, 'user_id')
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 1)
            for call in mock_send.call_args_list:
                self.assertEqual(call[0][0], ['user_id'])

    def test_event_schedule(self):
        # Insert a Subscription for this Event
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.SCHEDULE_UPDATED]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.event_schedule(self.event)
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 1)
            user_ids = mock_send.call_args[0][0]
            self.assertEqual(user_ids, ['user_id_1'])
            notification = mock_send.call_args[0][1]
            self.assertTrue(isinstance(notification, EventScheduleNotification))
            self.assertEqual(notification.event, self.event)

    def test_match_score_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_score(self.match)
            mock_send.assert_not_called()

    def test_match_score_user_id(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [Team(id="frc%s" % team_number, team_number=team_number) for team_number in range(6)]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send, patch.object(TBANSHelper, 'schedule_upcoming_match') as schedule_upcoming_match:
            TBANSHelper.match_score(self.match, 'user_id')
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            for call in mock_send.call_args_list:
                self.assertEqual(call[0][0], ['user_id'])
            # Make sure we called upcoming_match with the same user_id
            schedule_upcoming_match.assert_called()
            self.assertEqual(len(schedule_upcoming_match.call_args_list), 1)
            self.assertEqual(schedule_upcoming_match.call_args[0][1], 'user_id')

    def test_match_score(self):
        # Insert a Subscription for this Event, Team, and Match so we call to send
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.MATCH_SCORE]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.MATCH_SCORE]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_3'),
            user_id='user_id_3',
            model_key=self.match.key_name,
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.MATCH_SCORE]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_score(self.match)
            # Three calls total - First to the Event, second to Team frc7332, third to Match 2020miket_qm1
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            self.assertEqual([x[0] for x in [call[0][0] for call in mock_send.call_args_list]], ['user_id_1', 'user_id_2', 'user_id_3'])
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                self.assertTrue(isinstance(notification, MatchScoreNotification))
                self.assertEqual(notification.match, self.match)
            # Check frc7332 notification
            notification = notifications[1]
            self.assertEqual(notification.team, self.team)

    def test_match_score_match_upcoming(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [Team(id="frc%s" % team_number, team_number=team_number) for team_number in range(6)]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        from helpers.match_helper import MatchHelper
        next_matches = MatchHelper.upcomingMatches(self.event.matches, num=2)

        with patch.object(TBANSHelper, 'schedule_upcoming_match') as schedule_upcoming_match:
            TBANSHelper.match_score(self.match)
            schedule_upcoming_match.assert_called()
            self.assertEqual(len(schedule_upcoming_match.call_args_list), 1)
            self.assertEqual(len(schedule_upcoming_match.call_args), 2)
            self.assertEqual(schedule_upcoming_match.call_args[0][0], next_matches.pop())
            self.assertIsNone(schedule_upcoming_match.call_args[0][1])

    def test_match_upcoming_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_upcoming(self.match)
            mock_send.assert_not_called()

    def test_match_upcoming_user_id(self):
        # Set our match to be 1-1 so we can test event_level
        self.match.set_number = 1
        self.match.match_number = 1

        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send, patch.object(TBANSHelper, 'event_level') as mock_event_level:
            TBANSHelper.match_upcoming(self.match, 'user_id')
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            for call in mock_send.call_args_list:
                self.assertEqual(call[0][0], ['user_id'])
            # Make sure we called event_level with the same user_id
            mock_event_level.assert_called()
            self.assertEqual(len(mock_event_level.call_args_list), 1)
            self.assertEqual(mock_event_level.call_args[0][1], 'user_id')

    def test_match_upcoming(self):
        # Insert a Subscription for this Event, Team, and Match so we call to send
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_3'),
            user_id='user_id_3',
            model_key=self.match.key_name,
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_upcoming(self.match)
            # Three calls total - First to the Event, second to Team frc7332, third to Match 2020miket_qm1
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            self.assertEqual([x[0] for x in [call[0][0] for call in mock_send.call_args_list]], ['user_id_1', 'user_id_2', 'user_id_3'])
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                self.assertTrue(isinstance(notification, MatchUpcomingNotification))
                self.assertEqual(notification.match, self.match)
            # Check frc7332 notification
            notification = notifications[1]
            self.assertEqual(notification.team, self.team)

    def test_match_upcoming_event_level(self):
        # Make sure we call event_level for a 1-1 match_upcoming
        self.match.set_number = 1
        self.match.match_number = 1

        with patch.object(TBANSHelper, 'event_level') as mock_event_level:
            TBANSHelper.match_upcoming(self.match)
            mock_event_level.assert_called()
            self.assertEqual(len(mock_event_level.call_args_list), 1)
            self.assertEqual(mock_event_level.call_args[0][0], self.match)
            self.assertIsNone(mock_event_level.call_args[0][1])

    def test_match_video_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_video(self.match)
            mock_send.assert_not_called()

    def test_match_video_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_video(self.match, 'user_id')
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            for call in mock_send.call_args_list:
                self.assertEqual(call[0][0], ['user_id'])

    def test_match_video(self):
        # Insert a Subscription for this Event, Team, and Match so we call to send
        Subscription(
            parent=ndb.Key(Account, 'user_id_1'),
            user_id='user_id_1',
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.MATCH_VIDEO]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_2'),
            user_id='user_id_2',
            model_key='frc7332',
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.MATCH_VIDEO]
        ).put()
        Subscription(
            parent=ndb.Key(Account, 'user_id_3'),
            user_id='user_id_3',
            model_key=self.match.key_name,
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.MATCH_VIDEO]
        ).put()

        with patch.object(TBANSHelper, '_send') as mock_send:
            TBANSHelper.match_video(self.match)
            # Three calls total - First to the Event, second to Team frc7332, third to Match 2020miket_qm1
            mock_send.assert_called()
            self.assertEqual(len(mock_send.call_args_list), 3)
            self.assertEqual([x[0] for x in [call[0][0] for call in mock_send.call_args_list]], ['user_id_1', 'user_id_2', 'user_id_3'])
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                self.assertTrue(isinstance(notification, MatchVideoNotification))
                self.assertEqual(notification.match, self.match)
            # Check frc7332 notification
            notification = notifications[1]
            self.assertEqual(notification.team, self.team)

    def test_ping_client(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone')

        with patch.object(TBANSHelper, '_ping_client', return_value=True) as mock_ping_client:
            success = TBANSHelper.ping(client)
            mock_ping_client.assert_called_once_with(client)
            self.assertTrue(success)

    def test_ping_webhook(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='https://thebluealliance.com',
            client_type=ClientType.WEBHOOK,
            secret='secret',
            display_name='Webhook')

        with patch.object(TBANSHelper, '_ping_webhook', return_value=True) as mock_ping_webhook:
            success = TBANSHelper.ping(client)
            mock_ping_webhook.assert_called_once_with(client)
            self.assertTrue(success)

    def test_ping_fcm(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone')

        batch_response = messaging.BatchResponse([messaging.SendResponse({'name': 'abc'}, None)])
        with patch.object(FCMRequest, 'send', return_value=batch_response) as mock_send:
            success = TBANSHelper._ping_client(client)
            mock_send.assert_called_once()
            self.assertTrue(success)

    def test_ping_fcm_fail(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=ClientType.OS_IOS,
            device_uuid='uuid',
            display_name='Phone')

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, FirebaseError(500, 'testing'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response) as mock_send:
            success = TBANSHelper._ping_client(client)
            mock_send.assert_called_once()
            self.assertFalse(success)

    def test_ping_android(self):
        client_type = ClientType.OS_ANDROID
        messaging_id = 'token'

        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id=messaging_id,
            client_type=client_type,
            device_uuid='uuid',
            display_name='Phone')

        from notifications.ping import PingNotification
        with patch.object(PingNotification, 'send') as mock_send:
            success = TBANSHelper._ping_client(client)
            mock_send.assert_called_once_with({client_type: [messaging_id]})
            self.assertTrue(success)

    def test_ping_fcm_unsupported(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='token',
            client_type=-1,
            device_uuid='uuid',
            display_name='Phone')

        with self.assertRaises(Exception, msg='Unsupported FCM client type: -1'):
            TBANSHelper._ping_client(client)

    def test_ping_webhook_success(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='https://thebluealliance.com',
            client_type=ClientType.WEBHOOK,
            secret='secret',
            display_name='Webhook')

        from models.notifications.requests.webhook_request import WebhookRequest
        with patch.object(WebhookRequest, 'send', return_value=True) as mock_send:
            success = TBANSHelper._ping_webhook(client)
            mock_send.assert_called_once()
            self.assertTrue(success)

    def test_ping_webhook_failure(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='https://thebluealliance.com',
            client_type=ClientType.WEBHOOK,
            secret='secret',
            display_name='Webhook')

        from models.notifications.requests.webhook_request import WebhookRequest
        with patch.object(WebhookRequest, 'send', return_value=False) as mock_send:
            success = TBANSHelper._ping_webhook(client)
            mock_send.assert_called_once()
            self.assertFalse(success)

    def test_schedule_upcoming_matches(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [Team(id="frc%s" % team_number, team_number=team_number) for team_number in range(6)]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        with patch.object(TBANSHelper, 'schedule_upcoming_match') as mock_schedule_upcoming_match:
            TBANSHelper.schedule_upcoming_matches(self.event)
            mock_schedule_upcoming_match.assert_called()
            self.assertEqual(len(mock_schedule_upcoming_match.call_args_list), 2)

    def test_schedule_upcoming_matches_user_id(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [Team(id="frc%s" % team_number, team_number=team_number) for team_number in range(6)]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        with patch.object(TBANSHelper, 'schedule_upcoming_match') as mock_schedule_upcoming_match:
            TBANSHelper.schedule_upcoming_matches(self.event, 'user_id')
            mock_schedule_upcoming_match.assert_called()
            self.assertEqual(['user_id', 'user_id'], [args[0][1] for args in mock_schedule_upcoming_match.call_args_list])

    def test_schedule_upcoming_match_send(self):
        with patch.object(TBANSHelper, 'match_upcoming') as mock_match_upcoming:
            TBANSHelper.schedule_upcoming_match(self.match)
            mock_match_upcoming.assert_called_once_with(self.match, None)

    def test_schedule_upcoming_match_send_user_id(self):
        with patch.object(TBANSHelper, 'match_upcoming') as mock_match_upcoming:
            TBANSHelper.schedule_upcoming_match(self.match, 'user_id')
            mock_match_upcoming.assert_called_once_with(self.match, 'user_id')

    def test_schedule_upcoming_match_cancel(self):
        # Schedule a dummy task with the same name as the task we're about to schedule
        task_name = '{}_match_upcoming'.format(self.match.key_name)
        taskqueue.Task(name=task_name).add('push-notifications')
        # Sanity check - make sure we have scheduled a task
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)
        # Make sure after calling our schedule_upcoming_match we delete the previously-scheduled task
        TBANSHelper.schedule_upcoming_match(self.match)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_schedule_upcoming_match_defer(self):
        # Sanity check - make sure there are no existing tasks in the queue
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

        self.match.time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        # Make sure after calling our schedule_upcoming_match we defer the task
        TBANSHelper.schedule_upcoming_match(self.match)

        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, 'match_upcoming') as mockmatch_upcoming:
            deferred.run(tasks[0].payload)
            mockmatch_upcoming.assert_called_once_with(self.match, None)

    def test_schedule_upcoming_match_defer_user_id(self):
        # Sanity check - make sure there are no existing tasks in the queue
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

        self.match.time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        # Make sure after calling our schedule_upcoming_match we defer the task
        TBANSHelper.schedule_upcoming_match(self.match, 'user_id')

        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, 'match_upcoming') as mockmatch_upcoming:
            deferred.run(tasks[0].payload)
            mockmatch_upcoming.assert_called_once_with(self.match, 'user_id')

    def test_verification(self):
        from models.notifications.requests.webhook_request import WebhookRequest
        with patch.object(WebhookRequest, 'send') as mock_send:
            verification_key = TBANSHelper.verify_webhook('https://thebluealliance.com', 'secret')
            mock_send.assert_called_once()
            self.assertIsNotNone(verification_key)

    def test_send_empty(self):
        notification = MockNotification()
        with patch.object(TBANSHelper, '_defer_fcm') as mock_fcm, patch.object(TBANSHelper, '_defer_webhook') as mock_webhook:
            TBANSHelper._send([], notification)
            mock_fcm.assert_not_called()
            mock_webhook.assert_not_called()

    def test_send(self):
        expected = ['client_type_{}'.format(client_type) for client_type in ClientType.FCM_CLIENTS]
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='client_type_{}'.format(client_type),
                    client_type=client_type) for client_type in ClientType.names.keys()]
        # Insert an unverified webhook, just to test
        unverified = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='client_type_2',
            client_type=ClientType.WEBHOOK,
            verified=False)
        unverified.put()
        for c in clients:
            c.put()

        expected_fcm = [c for c in clients if c.client_type in ClientType.FCM_CLIENTS]
        expected_webhook = [c for c in clients if c.client_type == ClientType.WEBHOOK]

        notification = MockNotification()
        with patch.object(TBANSHelper, '_defer_fcm') as mock_fcm, patch.object(TBANSHelper, '_defer_webhook') as mock_webhook:
            TBANSHelper._send(['user_id'], notification)
            mock_fcm.assert_called_once_with(expected_fcm, notification)
            mock_webhook.assert_called_once_with(expected_webhook, notification)

    def test_defer_fcm(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='messaging_id',
            client_type=ClientType.OS_IOS)
        client.put()
        notification = MockNotification()
        TBANSHelper._defer_fcm([client], notification)

        # Make sure we'll send to FCM clients
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, '_send_fcm') as mock_send_fcm:
            deferred.run(tasks[0].payload)
            mock_send_fcm.assert_called_once_with([client], ANY)

    def test_defer_webhook(self):
        client = MobileClient(
            parent=ndb.Key(Account, 'user_id'),
            user_id='user_id',
            messaging_id='messaging_id',
            client_type=ClientType.WEBHOOK)
        client.put()
        notification = MockNotification()
        TBANSHelper._defer_webhook([client], notification)

        # Make sure we'll send to FCM clients
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, '_send_webhook') as mock_send_webhook:
            deferred.run(tasks[0].payload)
            mock_send_webhook.assert_called_once_with([client], ANY)

    def test_send_fcm_disabled(self):
        from sitevars.notifications_enable import NotificationsEnable
        NotificationsEnable.enable_notifications(False)

        with patch.object(NotificationsEnable, 'notifications_enabled', wraps=NotificationsEnable.notifications_enabled) as mock_check_enabled:
            exit_code = TBANSHelper._send_fcm([], MockNotification())
            mock_check_enabled.assert_called_once()
            self.assertEqual(exit_code, 1)

    def test_send_fcm_maximum_backoff(self):
        for i in range(0, 6):
            exit_code = TBANSHelper._send_fcm([], MockNotification(), backoff_iteration=i)
            self.assertEqual(exit_code, 0)

        # Backoff should start failing at 6
        exit_code = TBANSHelper._send_fcm([], MockNotification(), backoff_iteration=6)
        self.assertEqual(exit_code, 2)

    def test_send_fcm_filter_fcm_clients(self):
        expected = ['client_type_{}'.format(client_type) for client_type in ClientType.FCM_CLIENTS]
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='client_type_{}'.format(client_type),
                    client_type=client_type) for client_type in ClientType.names.keys()]

        with patch('models.notifications.requests.fcm_request.FCMRequest', autospec=True) as mock_init:
            exit_code = TBANSHelper._send_fcm(clients, MockNotification())
            mock_init.assert_called_once_with(ANY, ANY, expected)
            self.assertEqual(exit_code, 0)

    def test_send_fcm_batch(self):
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='{}'.format(i),
                    client_type=ClientType.OS_IOS) for i in range(3)]

        batch_response = messaging.BatchResponse([])
        with patch('models.notifications.requests.fcm_request.MAXIMUM_TOKENS', 2), patch.object(FCMRequest, 'send', return_value=batch_response) as mock_send:
            exit_code = TBANSHelper._send_fcm(clients, MockNotification())
            self.assertEqual(mock_send.call_count, 2)
            self.assertEqual(exit_code, 0)

    def test_send_fcm_unregister_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, UnregisteredError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), \
            patch.object(MobileClient, 'delete_for_messaging_id', wraps=MobileClient.delete_for_messaging_id) as mock_delete, \
                patch('logging.info') as mock_info:
                    exit_code = TBANSHelper._send_fcm([client], MockNotification())
                    mock_delete.assert_called_once_with('messaging_id')
                    self.assertEqual(exit_code, 0)
                    mock_info.assert_called_with('Deleting unregistered client with ID: messaging_id')

        # TODO: Check logging?

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), [])

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_send_fcm_sender_id_mismatch_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, SenderIdMismatchError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), \
            patch.object(MobileClient, 'delete_for_messaging_id', wraps=MobileClient.delete_for_messaging_id) as mock_delete, \
                patch('logging.info') as mock_info:
                    exit_code = TBANSHelper._send_fcm([client], MockNotification())
                    mock_delete.assert_called_once_with('messaging_id')
                    self.assertEqual(exit_code, 0)
                    mock_info.assert_called_with('Deleting mismatched client with ID: messaging_id')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), [])

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_send_fcm_quota_exceeded_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, QuotaExceededError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.error') as mock_error:
            exit_code = TBANSHelper._send_fcm([client], MockNotification())
            self.assertEqual(exit_code, 0)
            mock_error.assert_called_once_with('Qutoa exceeded - retrying client...')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        # Check that we queue'd for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, '_send_fcm') as mock_send_fcm:
            deferred.run(tasks[0].payload)
            mock_send_fcm.assert_called_once_with([client], ANY, 1)

    def test_send_fcm_third_party_auth_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, ThirdPartyAuthError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.critical') as mock_critical:
            exit_code = TBANSHelper._send_fcm([client], MockNotification())
            self.assertEqual(exit_code, 0)
            mock_critical.assert_called_once_with('Third party error sending to FCM - code')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_send_fcm_invalid_argument_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, InvalidArgumentError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.critical') as mock_critical:
            exit_code = TBANSHelper._send_fcm([client], MockNotification())
            self.assertEqual(exit_code, 0)
            mock_critical.assert_called_once_with('Invalid argument when sending to FCM - code')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_send_fcm_internal_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, InternalError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.error') as mock_error:
            exit_code = TBANSHelper._send_fcm([client], MockNotification())
            self.assertEqual(exit_code, 0)
            mock_error.assert_called_once_with('Interal FCM error - retrying client...')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        # Check that we queue'd for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, '_send_fcm') as mock_send_fcm:
            deferred.run(tasks[0].payload)
            mock_send_fcm.assert_called_once_with([client], ANY, 1)

    def test_send_fcm_unavailable_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, UnavailableError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.error') as mock_error:
            exit_code = TBANSHelper._send_fcm([client], MockNotification())
            self.assertEqual(exit_code, 0)
            mock_error.assert_called_once_with('FCM unavailable - retrying client...')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        # Check that we queue'd for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 1)

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, '_send_fcm') as mock_send_fcm:
            deferred.run(tasks[0].payload)
            mock_send_fcm.assert_called_once_with([client], ANY, 1)

    def test_send_fcm_unhandled_error(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, FirebaseError('code', 'message'))])
        with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.error') as mock_error:
            exit_code = TBANSHelper._send_fcm([client], MockNotification())
            self.assertEqual(exit_code, 0)
            mock_error.assert_called_once_with('Unhandled FCM error for messaging_id - code / message')

        # Sanity check
        self.assertEqual(fcm_messaging_ids('user_id'), ['messaging_id'])

        # Check that we didn't queue for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
        self.assertEqual(len(tasks), 0)

    def test_send_fcm_retry_backoff_time(self):
        client = MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='messaging_id',
                    client_type=ClientType.OS_IOS)
        client.put()

        import time

        batch_response = messaging.BatchResponse([messaging.SendResponse(None, QuotaExceededError('code', 'message'))])
        for i in range(0, 6):
            with patch.object(FCMRequest, 'send', return_value=batch_response), patch('logging.error'):
                call_time = time.time()
                TBANSHelper._send_fcm([client], MockNotification(), i)

                # Check that we queue'd for a retry with the proper countdown time
                tasks = self.taskqueue_stub.get_filtered_tasks(queue_names='push-notifications')
                if i > 0:
                    self.assertGreater(tasks[0].eta_posix - call_time, 0)

                # Make sure our taskqueue tasks execute what we expect
                with patch.object(TBANSHelper, '_send_fcm') as mock_send_fcm:
                    deferred.run(tasks[0].payload)
                    mock_send_fcm.assert_called_once_with([client], ANY, i + 1)

                self.taskqueue_stub.FlushQueue('push-notifications')

    def test_send_webhook_disabled(self):
        from sitevars.notifications_enable import NotificationsEnable
        NotificationsEnable.enable_notifications(False)

        with patch.object(NotificationsEnable, 'notifications_enabled', wraps=NotificationsEnable.notifications_enabled) as mock_check_enabled:
            exit_code = TBANSHelper._send_webhook([], MockNotification())
            mock_check_enabled.assert_called_once()
            self.assertEqual(exit_code, 1)

    def test_send_webhook_filter_webhook_clients(self):
        expected = 'client_type_{}'.format(ClientType.WEBHOOK)
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='client_type_{}'.format(client_type),
                    client_type=client_type) for client_type in ClientType.names.keys()]

        with patch('models.notifications.requests.webhook_request.WebhookRequest', autospec=True) as mock_init:
            exit_code = TBANSHelper._send_webhook(clients, MockNotification())
            mock_init.assert_called_once_with(ANY, expected, ANY)
            self.assertEqual(exit_code, 0)

    def test_send_webhook_filter_webhook_clients_verified(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, 'user_id'),
                user_id='user_id',
                messaging_id='unverified',
                client_type=ClientType.WEBHOOK,
                verified=False),
            MobileClient(
                parent=ndb.Key(Account, 'user_id'),
                user_id='user_id',
                messaging_id='verified',
                client_type=ClientType.WEBHOOK,
                verified=True)
        ]

        with patch('models.notifications.requests.webhook_request.WebhookRequest', autospec=True) as mock_init:
            exit_code = TBANSHelper._send_webhook(clients, MockNotification())
            mock_init.assert_called_once_with(ANY, 'verified', ANY)
            self.assertEqual(exit_code, 0)

    def test_send_webhook_multiple(self):
        clients = [MobileClient(
                    parent=ndb.Key(Account, 'user_id'),
                    user_id='user_id',
                    messaging_id='{}'.format(i),
                    client_type=ClientType.WEBHOOK) for i in range(3)]

        batch_response = messaging.BatchResponse([])
        with patch.object(WebhookRequest, 'send', return_value=batch_response) as mock_send:
            exit_code = TBANSHelper._send_webhook(clients, MockNotification())
            self.assertEqual(mock_send.call_count, 3)
            self.assertEqual(exit_code, 0)

    def test_debug_string(self):
        exception = FirebaseError('code', 'message')
        self.assertEqual(TBANSHelper._debug_string(exception), 'code / message')

    def test_debug_string_response(self):
        class MockResponse:
            def json(self):
                import json
                return json.dumps({'mock': 'mock'})
        exception = FirebaseError('code', 'message', None, MockResponse())
        self.assertEqual(TBANSHelper._debug_string(exception), 'code / message / {"mock": "mock"}')
