import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
from unittest.mock import ANY, patch

import pytest
from firebase_admin import messaging
from firebase_admin.exceptions import (
    FirebaseError,
    InternalError,
    InvalidArgumentError,
    UnavailableError,
)
from firebase_admin.messaging import (
    QuotaExceededError,
    SenderIdMismatchError,
    ThirdPartyAuthError,
    UnregisteredError,
)
from google.appengine.api.taskqueue import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from backend.common.consts.award_type import AwardType
from backend.common.consts.client_type import (
    ClientType,
    FCM_CLIENTS,
)
from backend.common.consts.client_type import NAMES as CLIENT_TYPE_NAMES
from backend.common.consts.event_type import EventType
from backend.common.consts.model_type import ModelType
from backend.common.consts.notification_type import NotificationType
from backend.common.helpers.tbans_helper import _firebase_app, TBANSHelper
from backend.common.models.account import Account
from backend.common.models.award import Award
from backend.common.models.event_details import EventDetails
from backend.common.models.match import Match
from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.alliance_selection import (
    AllianceSelectionNotification,
)
from backend.common.models.notifications.awards import AwardsNotification
from backend.common.models.notifications.broadcast import BroadcastNotification
from backend.common.models.notifications.event_level import (
    EventLevelNotification,
)
from backend.common.models.notifications.event_schedule import (
    EventScheduleNotification,
)
from backend.common.models.notifications.match_score import (
    MatchScoreNotification,
)
from backend.common.models.notifications.match_upcoming import (
    MatchUpcomingNotification,
)
from backend.common.models.notifications.match_video import (
    MatchVideoNotification,
)
from backend.common.models.notifications.mytba import (
    FavoritesUpdatedNotification,
    SubscriptionsUpdatedNotification,
)
from backend.common.models.notifications.requests.fcm_request import FCMRequest
from backend.common.models.notifications.requests.webhook_request import (
    WebhookRequest,
)
from backend.common.models.notifications.tests.mocks.notifications.mock_notification import (
    MockNotification,
)
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team
from backend.common.queries.mobile_client_query import MobileClientQuery
from backend.common.tests.creators.event_test_creator import EventTestCreator
from backend.common.tests.creators.match_test_creator import MatchTestCreator


def fcm_messaging_ids(user_id):
    clients = MobileClient.query(
        MobileClient.client_type.IN(FCM_CLIENTS), ancestor=ndb.Key(Account, user_id)
    ).fetch(projection=[MobileClient.messaging_id])
    return [c.messaging_id for c in clients]


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestTBANSHelper(unittest.TestCase):
    def setUp(self):
        self.gae_testbed = testbed.Testbed()
        self.gae_testbed.activate()

        self.gae_testbed.init_taskqueue_stub(root_path="src/")
        self.taskqueue_stub = self.gae_testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        self.event = EventTestCreator.create_future_event()
        self.team = Team(id="frc7332", team_number=7332)
        self.team.put()
        self.match = Match(
            id="2020miket_qm1",
            event=self.event.key,
            comp_level="qm",
            set_number=1,
            match_number=1,
            team_key_names=["frc7332"],
            alliances_json=json.dumps(
                {
                    "red": {
                        "teams": ["frc1", "frc2", "frc7332"],
                        "score": -1,
                    },
                    "blue": {
                        "teams": ["frc4", "frc5", "frc6"],
                        "score": -1,
                    },
                }
            ),
            year=2020,
        )

    def tearDown(self):
        self.gae_testbed.deactivate()

    def test_firebase_app(self):
        # Make sure we can get an original Firebase app
        app_one = _firebase_app()
        assert app_one is not None
        assert app_one.name == "tbans"
        # Make sure duplicate calls don't crash
        app_two = _firebase_app()
        assert app_two is not None
        assert app_two.name == "tbans"
        # Should be the same object
        assert app_one == app_two

    def test_alliance_selection_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.alliance_selection(self.event)
            mock_send.assert_not_called()

    def test_alliance_selection_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.alliance_selection(self.event, "user_id")
            mock_send.assert_called_once()
            user_id = mock_send.call_args[0][0]
            assert user_id == ["user_id"]

    def test_alliance_selection(self):
        # Insert a Subscription for this Event and these Teams so we call to send
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key="frc1",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.ALLIANCE_SELECTION],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_2"),
            user_id="user_id_2",
            model_key="frc7332",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.ALLIANCE_SELECTION],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_3"),
            user_id="user_id_3",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.ALLIANCE_SELECTION],
        ).put()

        # Insert EventDetails for the event with alliance selection information
        EventDetails(
            id=self.event.key_name,
            alliance_selections=[{"declines": [], "picks": ["frc7332"]}],
        ).put()

        TBANSHelper.alliance_selection(self.event)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 2

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            TBANSHelper.alliance_selection(self.event)
            # Two calls total - First to the Event, second to frc7332, no call for frc1
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 2
            assert [
                x[0] for x in [call[0][0] for call in mock_send.call_args_list]
            ] == ["user_id_3", "user_id_2"]
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                assert isinstance(notification, AllianceSelectionNotification)
            # Check Event notification
            event_notification = notifications[0]
            assert event_notification.event == self.event
            assert event_notification.team is None
            # Check frc7332 notification
            team_notification = notifications[1]
            assert team_notification.event == self.event
            assert team_notification.team == self.team

    def test_awards_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.awards(self.event)
            mock_send.assert_not_called()

    def test_awards_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.awards(self.event, "user_id")
            mock_send.assert_called_once()
            user_id = mock_send.call_args[0][0]
            assert user_id == ["user_id"]

    def test_awards(self):
        # Insert some Awards for some Teams
        award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.INDUSTRIAL_DESIGN),
            name_str="Industrial Design Award sponsored by General Motors",
            award_type_enum=AwardType.INDUSTRIAL_DESIGN,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc7332")],
            year=2020,
        )
        award.put()
        winner_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.WINNER),
            name_str="Regional Event Winner",
            award_type_enum=AwardType.WINNER,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc7332"), ndb.Key(Team, "frc1")],
            year=2020,
        )
        winner_award.put()
        frc_1 = Team(id="frc1", team_number=1)
        frc_1.put()

        # Insert a Subscription for this Event and these Teams so we call to send
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key="frc1",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.AWARDS],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_2"),
            user_id="user_id_2",
            model_key="frc7332",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.AWARDS],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_3"),
            user_id="user_id_3",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.AWARDS],
        ).put()

        TBANSHelper.awards(self.event)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 3

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            # Three calls total - First to the Event, second to frc7332 (two awards), third to frc1 (one award)
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            assert [
                x[0] for x in [call[0][0] for call in mock_send.call_args_list]
            ] == ["user_id_3", "user_id_2", "user_id_1"]
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                assert isinstance(notification, AwardsNotification)
            # Check Event notification
            event_notification = notifications[0]
            assert event_notification.event == self.event
            assert event_notification.team is None
            assert event_notification.team_awards == []
            # Check frc7332 notification
            event_notification = notifications[1]
            assert event_notification.event == self.event
            assert event_notification.team == self.team
            assert len(event_notification.team_awards) == 2
            # Check frc1 notification
            event_notification = notifications[2]
            assert event_notification.event == self.event
            assert event_notification.team == frc_1
            assert len(event_notification.team_awards) == 1

    def test_broadcast_none(self):
        TBANSHelper.broadcast([], "Broadcast", "Test broadcast")

        # Make sure we didn't send to FCM or webhooks
        tasks = self.taskqueue_stub.GetTasks("push-notifications")
        assert len(tasks) == 0

    def test_broadcast_fcm_empty(self):
        for client_type in FCM_CLIENTS:
            TBANSHelper.broadcast([client_type], "Broadcast", "Test broadcast")

            # Make sure we didn't send to FCM or webhooks
            tasks = self.taskqueue_stub.GetTasks("push-notifications")
            assert len(tasks) == 0

    def test_broadcast_fcm(self):
        for client_type in FCM_CLIENTS:
            client = MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="token",
                client_type=client_type,
                device_uuid="uuid",
                display_name="Phone",
            )
            client_key = client.put()

            TBANSHelper.broadcast([client_type], "Broadcast", "Test broadcast")

            # Make sure we'll send to FCM clients
            tasks = self.taskqueue_stub.get_filtered_tasks(
                queue_names="push-notifications"
            )
            assert len(tasks) == 1

            # Make sure our taskqueue tasks execute what we expect
            with patch.object(TBANSHelper, "_send_fcm") as mock_send_fcm:
                deferred.run(tasks[0].payload)
                mock_send_fcm.assert_called_once_with([client], ANY, False)
                # Make sure the notification is a BroadcastNotification
                notification = mock_send_fcm.call_args[0][1]
                assert isinstance(notification, BroadcastNotification)

            self.taskqueue_stub.FlushQueue("push-notifications")

            client_key.delete()

    def test_broadcast_webhook_empty(self):
        TBANSHelper.broadcast([ClientType.WEBHOOK], "Broadcast", "Test broadcast")

        # Make sure we didn't send to FCM or webhooks
        tasks = self.taskqueue_stub.GetTasks("push-notifications")
        assert len(tasks) == 0

    def test_broadcast_webhook(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="token",
            client_type=ClientType.WEBHOOK,
            device_uuid="uuid",
            display_name="Phone",
        )
        client.put()

        TBANSHelper.broadcast([ClientType.WEBHOOK], "Broadcast", "Test broadcast")

        # Make sure we'll send to FCM clients
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, "_send_webhook") as mock_send_webhook:
            deferred.run(tasks[0].payload)
            mock_send_webhook.assert_called_once_with([client], ANY)
            # Make sure the notification is a BroadcastNotification
            notification = mock_send_webhook.call_args[0][1]
            assert isinstance(notification, BroadcastNotification)

    def test_event_level_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.event_level(self.match)
            mock_send.assert_not_called()

    def test_event_level_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.event_level(self.match, "user_id")
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 1
            for call in mock_send.call_args_list:
                assert call[0][0] == ["user_id"]

    def test_event_level(self):
        # Insert a Subscription for this Event
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.LEVEL_STARTING],
        ).put()

        TBANSHelper.event_level(self.match)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 1
            user_ids = mock_send.call_args[0][0]
            assert user_ids == ["user_id_1"]
            notification = mock_send.call_args[0][1]
            assert isinstance(notification, EventLevelNotification)
            assert notification.match == self.match
            assert notification.event == self.event

    def test_event_schedule_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.event_schedule(self.event)
            mock_send.assert_not_called()

    def test_event_schedule_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.event_schedule(self.event, "user_id")
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 1
            for call in mock_send.call_args_list:
                assert call[0][0] == ["user_id"]

    def test_event_schedule(self):
        # Insert a Subscription for this Event
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.SCHEDULE_UPDATED],
        ).put()

        TBANSHelper.event_schedule(self.event)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 1
            user_ids = mock_send.call_args[0][0]
            assert user_ids == ["user_id_1"]
            notification = mock_send.call_args[0][1]
            assert isinstance(notification, EventScheduleNotification)
            assert notification.event == self.event

    def test_match_score_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.match_score(self.match)
            mock_send.assert_not_called()

    def test_match_score_user_id(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [
            Team(id="frc%s" % team_number, team_number=team_number)
            for team_number in range(6)
        ]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send, patch.object(
            TBANSHelper, "schedule_upcoming_match"
        ) as schedule_upcoming_match:
            TBANSHelper.match_score(self.match, "user_id")
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            for call in mock_send.call_args_list:
                assert call[0][0] == ["user_id"]
            # Make sure we called upcoming_match with the same user_id
            schedule_upcoming_match.assert_called()
            assert len(schedule_upcoming_match.call_args_list) == 1
            assert schedule_upcoming_match.call_args[0][1] == "user_id"

    def test_match_score(self):
        # Insert a Subscription for this Event, Team, and Match so we call to send
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.MATCH_SCORE],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_2"),
            user_id="user_id_2",
            model_key="frc7332",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.MATCH_SCORE],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_3"),
            user_id="user_id_3",
            model_key=self.match.key_name,
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.MATCH_SCORE],
        ).put()

        TBANSHelper.match_score(self.match)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 3

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            # Three calls total - First to the Event, second to Team frc7332, third to Match 2020miket_qm1
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            assert [
                x[0] for x in [call[0][0] for call in mock_send.call_args_list]
            ] == ["user_id_1", "user_id_2", "user_id_3"]
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                assert isinstance(notification, MatchScoreNotification)
                assert notification.match == self.match
            # Check frc7332 notification
            notification = notifications[1]
            assert notification.team == self.team

    def test_match_score_match_upcoming(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [
            Team(id="frc%s" % team_number, team_number=team_number)
            for team_number in range(6)
        ]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        from backend.common.helpers.match_helper import MatchHelper

        next_matches = MatchHelper.upcoming_matches(self.event.matches, num=2)

        with patch.object(
            TBANSHelper, "schedule_upcoming_match"
        ) as schedule_upcoming_match:
            TBANSHelper.match_score(self.match)
            schedule_upcoming_match.assert_called()
            assert len(schedule_upcoming_match.call_args_list) == 1
            assert len(schedule_upcoming_match.call_args) == 2
            assert schedule_upcoming_match.call_args[0][0] == next_matches.pop()
            assert schedule_upcoming_match.call_args[0][1] is None

    def test_match_upcoming_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.match_upcoming(self.match)
            mock_send.assert_not_called()

    def test_match_upcoming_user_id(self):
        # Set our match to be 1-1 so we can test event_level
        self.match.set_number = 1
        self.match.match_number = 1

        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send, patch.object(
            TBANSHelper, "event_level"
        ) as mock_event_level:
            TBANSHelper.match_upcoming(self.match, "user_id")
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            for call in mock_send.call_args_list:
                assert call[0][0] == ["user_id"]
            # Make sure we called event_level with the same user_id
            mock_event_level.assert_called()
            assert len(mock_event_level.call_args_list) == 1
            assert mock_event_level.call_args[0][1] == "user_id"

    def test_match_upcoming(self):
        # Insert a Subscription for this Event, Team, and Match so we call to send
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.UPCOMING_MATCH],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_2"),
            user_id="user_id_2",
            model_key="frc7332",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.UPCOMING_MATCH],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_3"),
            user_id="user_id_3",
            model_key=self.match.key_name,
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.UPCOMING_MATCH],
        ).put()

        TBANSHelper.match_upcoming(self.match)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 3

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            # Three calls total - First to the Event, second to Team frc7332, third to Match 2020miket_qm1
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            assert [
                x[0] for x in [call[0][0] for call in mock_send.call_args_list]
            ] == ["user_id_1", "user_id_2", "user_id_3"]
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                assert isinstance(notification, MatchUpcomingNotification)
                assert notification.match == self.match
            # Check frc7332 notification
            notification = notifications[1]
            assert notification.team == self.team

    def test_match_upcoming_event_level(self):
        # Make sure we call event_level for a 1-1 match_upcoming
        self.match.set_number = 1
        self.match.match_number = 1

        with patch.object(TBANSHelper, "event_level") as mock_event_level:
            TBANSHelper.match_upcoming(self.match)
            mock_event_level.assert_called()
            assert len(mock_event_level.call_args_list) == 1
            assert mock_event_level.call_args[0][0] == self.match
            assert mock_event_level.call_args[0][1] is None

    def test_match_video_no_users(self):
        # Test send not called with no subscribed users
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.match_video(self.match)
            mock_send.assert_not_called()

    def test_match_video_user_id(self):
        # Test send called with user id
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.match_video(self.match, "user_id")
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            for call in mock_send.call_args_list:
                assert call[0][0] == ["user_id"]

    def test_match_video(self):
        # Insert a Subscription for this Event, Team, and Match so we call to send
        Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key=self.event.key_name,
            model_type=ModelType.EVENT,
            notification_types=[NotificationType.MATCH_VIDEO],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_2"),
            user_id="user_id_2",
            model_key="frc7332",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.MATCH_VIDEO],
        ).put()
        Subscription(
            parent=ndb.Key(Account, "user_id_3"),
            user_id="user_id_3",
            model_key=self.match.key_name,
            model_type=ModelType.MATCH,
            notification_types=[NotificationType.MATCH_VIDEO],
        ).put()

        TBANSHelper.match_video(self.match)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 3

        with patch.object(TBANSHelper, "_send") as mock_send:
            for task in tasks:
                deferred.run(task.payload)

            # Three calls total - First to the Event, second to Team frc7332, third to Match 2020miket_qm1
            mock_send.assert_called()
            assert len(mock_send.call_args_list) == 3
            assert [
                x[0] for x in [call[0][0] for call in mock_send.call_args_list]
            ] == ["user_id_1", "user_id_2", "user_id_3"]
            notifications = [call[0][1] for call in mock_send.call_args_list]
            for notification in notifications:
                assert isinstance(notification, MatchVideoNotification)
                assert notification.match == self.match
            # Check frc7332 notification
            notification = notifications[1]
            assert notification.team == self.team

    def test_update_favorites(self):
        user_id = "user_id_1"
        device_id = "device_id"

        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.update_favorites(user_id, device_id)
            assert mock_send.call_count == 1
            call_args = mock_send.call_args[0]
            assert call_args[0] == [user_id]
            assert isinstance(call_args[1], FavoritesUpdatedNotification)
            assert call_args[1].user_id == user_id

    def test_update_subscriptions(self):
        user_id = "user_id_1"
        device_id = "device_id"

        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper.update_subscriptions(user_id, device_id)
            assert mock_send.call_count == 1
            call_args = mock_send.call_args[0]
            assert call_args[0] == [user_id]
            assert isinstance(call_args[1], SubscriptionsUpdatedNotification)
            assert call_args[1].user_id == user_id

    def test_ping_client(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="token",
            client_type=ClientType.OS_IOS,
            device_uuid="uuid",
            display_name="Phone",
        )

        with patch.object(
            TBANSHelper, "_ping_client", return_value=True
        ) as mock_ping_client:
            success = TBANSHelper.ping(client)
            mock_ping_client.assert_called_once_with(client)
            assert success

    def test_ping_webhook(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="https://thebluealliance.com",
            client_type=ClientType.WEBHOOK,
            secret="secret",
            display_name="Webhook",
        )

        with patch.object(
            TBANSHelper, "_ping_webhook", return_value=True
        ) as mock_ping_webhook:
            success = TBANSHelper.ping(client)
            mock_ping_webhook.assert_called_once_with(client)
            assert success

    def test_ping_fcm(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="token",
            client_type=ClientType.OS_IOS,
            device_uuid="uuid",
            display_name="Phone",
        )

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse({"name": "abc"}, None)]
        )
        with patch.object(
            FCMRequest, "__init__", mock.MagicMock(spec=FCMRequest, return_value=None)
        ) as mock_fcm_request_constructor, patch.object(
            FCMRequest, "send", return_value=batch_response
        ) as mock_send:
            success = TBANSHelper._ping_client(client)

            mock_fcm_request_constructor.assert_called_once()
            mock_send.assert_called_once()
            assert success

    def test_ping_fcm_fail(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="token",
            client_type=ClientType.OS_IOS,
            device_uuid="uuid",
            display_name="Phone",
        )

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, FirebaseError(500, "testing"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response) as mock_send:
            success = TBANSHelper._ping_client(client)
            mock_send.assert_called_once()
            assert not success

    def test_ping_webhook_success(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="https://thebluealliance.com",
            client_type=ClientType.WEBHOOK,
            secret="secret",
            display_name="Webhook",
        )

        from backend.common.models.notifications.requests.webhook_request import (
            WebhookRequest,
        )

        with patch.object(WebhookRequest, "send", return_value=True) as mock_send:
            success = TBANSHelper._ping_webhook(client)
            mock_send.assert_called_once()
            assert success

    def test_ping_webhook_failure(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="https://thebluealliance.com",
            client_type=ClientType.WEBHOOK,
            secret="secret",
            display_name="Webhook",
        )

        from backend.common.models.notifications.requests.webhook_request import (
            WebhookRequest,
        )

        with patch.object(WebhookRequest, "send", return_value=False) as mock_send:
            success = TBANSHelper._ping_webhook(client)
            mock_send.assert_called_once()
            assert not success

    def test_schedule_upcoming_matches_not_new_schedule(self):
        # Set some upcoming matches for the Event - not Match 1 though, so no notification gets sent
        match_creator = MatchTestCreator(self.event)
        teams = [
            Team(id="frc%s" % team_number, team_number=team_number)
            for team_number in range(6)
        ]
        self.event._teams = teams
        match_creator.createIncompleteQuals()

        with patch.object(
            TBANSHelper, "schedule_upcoming_match"
        ) as mock_schedule_upcoming_match:
            TBANSHelper.schedule_upcoming_matches(self.event)
            mock_schedule_upcoming_match.assert_not_called()

    def test_schedule_upcoming_matches(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [
            Team(id="frc%s" % team_number, team_number=team_number)
            for team_number in range(6)
        ]
        self.event._teams = teams
        matches = match_creator.createIncompleteQuals()

        # Hack our first next upcoming match to be Match 1
        first_match = matches[0]
        first_match.match_number = 1
        first_match.put()

        with patch.object(
            TBANSHelper, "schedule_upcoming_match"
        ) as mock_schedule_upcoming_match:
            TBANSHelper.schedule_upcoming_matches(self.event)
            mock_schedule_upcoming_match.assert_called()
            assert len(mock_schedule_upcoming_match.call_args_list) == 2

    def test_schedule_upcoming_matches_user_id(self):
        # Set some upcoming matches for the Event
        match_creator = MatchTestCreator(self.event)
        teams = [
            Team(id="frc%s" % team_number, team_number=team_number)
            for team_number in range(6)
        ]
        self.event._teams = teams
        matches = match_creator.createIncompleteQuals()

        # Hack our first next upcoming match to be Match 1
        first_match = matches[0]
        first_match.match_number = 1
        first_match.put()

        with patch.object(
            TBANSHelper, "schedule_upcoming_match"
        ) as mock_schedule_upcoming_match:
            TBANSHelper.schedule_upcoming_matches(self.event, "user_id")
            mock_schedule_upcoming_match.assert_called()
            assert ["user_id", "user_id"] == [
                args[0][1] for args in mock_schedule_upcoming_match.call_args_list
            ]

    def test_schedule_upcoming_match_send(self):
        with patch.object(TBANSHelper, "match_upcoming") as mock_match_upcoming:
            TBANSHelper.schedule_upcoming_match(self.match)
            mock_match_upcoming.assert_called_once_with(self.match, None)

    def test_schedule_upcoming_match_send_user_id(self):
        with patch.object(TBANSHelper, "match_upcoming") as mock_match_upcoming:
            TBANSHelper.schedule_upcoming_match(self.match, "user_id")
            mock_match_upcoming.assert_called_once_with(self.match, "user_id")

    def test_schedule_upcoming_match_cancel(self):
        # Schedule a dummy task with the same name as the task we're about to schedule
        task_name = "{}_match_upcoming".format(self.match.key_name)
        taskqueue.Task(name=task_name).add("push-notifications")
        # Sanity check - make sure we have scheduled a task
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1
        # Make sure after calling our schedule_upcoming_match we delete the previously-scheduled task
        TBANSHelper.schedule_upcoming_match(self.match)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

    def test_schedule_upcoming_match_defer(self):
        # Sanity check - make sure there are no existing tasks in the queue
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

        self.match.time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            hours=1
        )
        # Make sure after calling our schedule_upcoming_match we defer the task
        TBANSHelper.schedule_upcoming_match(self.match)

        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, "match_upcoming") as mockmatch_upcoming:
            deferred.run(tasks[0].payload)
            mockmatch_upcoming.assert_called_once_with(self.match, None)

    def test_schedule_upcoming_match_defer_user_id(self):
        # Sanity check - make sure there are no existing tasks in the queue
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

        self.match.time = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            hours=1
        )
        # Make sure after calling our schedule_upcoming_match we defer the task
        TBANSHelper.schedule_upcoming_match(self.match, "user_id")

        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, "match_upcoming") as mockmatch_upcoming:
            deferred.run(tasks[0].payload)
            mockmatch_upcoming.assert_called_once_with(self.match, "user_id")

    def test_verification(self):
        from backend.common.models.notifications.requests.webhook_request import (
            WebhookRequest,
        )

        with patch.object(WebhookRequest, "send") as mock_send:
            verification_key = TBANSHelper.verify_webhook(
                "https://thebluealliance.com", "secret"
            )
            mock_send.assert_called_once()
            assert verification_key is not None

    def test_send_empty(self):
        notification = MockNotification()
        with patch.object(TBANSHelper, "_defer_fcm") as mock_fcm, patch.object(
            TBANSHelper, "_defer_webhook"
        ) as mock_webhook:
            TBANSHelper._send([], notification)
            mock_fcm.assert_not_called()
            mock_webhook.assert_not_called()

    def test_send(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="client_type_{}".format(client_type),
                client_type=client_type,
            )
            for client_type in CLIENT_TYPE_NAMES.keys()
        ]
        # Insert an unverified webhook, just to test
        unverified = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="client_type_2",
            client_type=ClientType.WEBHOOK,
            verified=False,
        )
        unverified.put()
        for c in clients:
            c.put()

        expected_fcm = [c for c in clients if c.client_type in FCM_CLIENTS]
        expected_webhook = [c for c in clients if c.client_type == ClientType.WEBHOOK]

        notification = MockNotification()
        with patch.object(TBANSHelper, "_defer_fcm") as mock_fcm, patch.object(
            TBANSHelper, "_defer_webhook"
        ) as mock_webhook:
            TBANSHelper._send(["user_id"], notification)
            mock_fcm.assert_called_once_with(expected_fcm, notification)
            mock_webhook.assert_called_once_with(expected_webhook, notification)

    def test_defer_fcm(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()
        notification = MockNotification()
        TBANSHelper._defer_fcm([client], notification)

        # Make sure we'll send to FCM clients
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, "_send_fcm") as mock_send_fcm:
            deferred.run(tasks[0].payload)
            mock_send_fcm.assert_called_once_with([client], ANY, False)

    def test_defer_webhook(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.WEBHOOK,
        )
        client.put()
        notification = MockNotification()
        TBANSHelper._defer_webhook([client], notification)

        # Make sure we'll send to FCM clients
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        with patch.object(TBANSHelper, "_send_webhook") as mock_send_webhook:
            deferred.run(tasks[0].payload)
            mock_send_webhook.assert_called_once_with([client], ANY)

    def test_send_fcm_disabled(self):
        from backend.common.sitevars.notifications_enable import NotificationsEnable

        NotificationsEnable.enable_notifications(False)

        with patch.object(
            NotificationsEnable,
            "notifications_enabled",
            wraps=NotificationsEnable.notifications_enabled,
        ) as mock_check_enabled:
            TBANSHelper._send_fcm([], MockNotification())
            mock_check_enabled.assert_called_once()

    # def test_send_fcm_maximum_backoff(self):
    #     for i in range(0, 6):
    #         TBANSHelper._send_fcm([], MockNotification(), backoff_iteration=i)
    #
    #     # Backoff should start failing at 6
    #     # TODO: Exit codes were removed - should check we don't call send
    #     TBANSHelper._send_fcm([], MockNotification(), backoff_iteration=6)

    def test_send_fcm_filter_fcm_clients(self):
        expected = ["client_type_{}".format(client_type) for client_type in FCM_CLIENTS]
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="client_type_{}".format(client_type),
                client_type=client_type,
            )
            for client_type in CLIENT_TYPE_NAMES.keys()
        ]

        with patch(
            "backend.common.models.notifications.requests.fcm_request.FCMRequest",
            autospec=True,
        ) as mock_init:
            TBANSHelper._send_fcm(clients, MockNotification())
            mock_init.assert_called_once_with(ANY, ANY, expected, False)

    def test_send_fcm_filter_from_notification(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="client_type_{}".format(client_type),
                client_type=client_type,
            )
            for client_type in CLIENT_TYPE_NAMES.keys()
        ]

        with patch(
            "backend.common.models.notifications.requests.fcm_request.FCMRequest",
            autospec=True,
        ) as mock_init:
            TBANSHelper._send_fcm(clients, MockNotification(should_send=False))
            mock_init.assert_not_called()

    def test_send_fcm_batch(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="{}".format(i),
                client_type=ClientType.OS_IOS,
            )
            for i in range(3)
        ]

        batch_response = messaging.BatchResponse([])
        with patch(
            "backend.common.models.notifications.requests.fcm_request.MAXIMUM_TOKENS",
            2,
        ), patch.object(FCMRequest, "send", return_value=batch_response) as mock_send:
            TBANSHelper._send_fcm(clients, MockNotification())
            assert mock_send.call_count == 2

    def test_send_fcm_unregister_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, UnregisteredError("code", "message"))]
        )
        with patch.object(
            FCMRequest, "send", return_value=batch_response
        ), patch.object(
            MobileClientQuery,
            "delete_for_messaging_id",
            wraps=MobileClientQuery.delete_for_messaging_id,
        ) as mock_delete:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_delete.assert_called_once_with("messaging_id")

        # Sanity check
        assert fcm_messaging_ids("user_id") == []

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

    def test_send_fcm_sender_id_mismatch_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, SenderIdMismatchError("code", "message"))]
        )
        with patch.object(
            FCMRequest, "send", return_value=batch_response
        ), patch.object(
            MobileClientQuery,
            "delete_for_messaging_id",
            wraps=MobileClientQuery.delete_for_messaging_id,
        ) as mock_delete:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_delete.assert_called_once_with("messaging_id")

        # Sanity check
        assert fcm_messaging_ids("user_id") == []

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

    def test_send_fcm_quota_exceeded_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, QuotaExceededError("code", "message"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response), patch(
            "logging.error"
        ) as mock_error:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_error.assert_called_once_with("Qutoa exceeded - retrying client...")

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        # Check that we queue'd for a retry
        # NOTE: Removed in https://github.com/the-blue-alliance/the-blue-alliance/pull/4620
        # tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        # assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        # with patch.object(TBANSHelper, "_send_fcm") as mock_send_fcm:
        #     deferred.run(tasks[0].payload)
        #     mock_send_fcm.assert_called_once_with([client], ANY, False, 1)

    def test_send_fcm_third_party_auth_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, ThirdPartyAuthError("code", "message"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response), patch(
            "logging.critical"
        ) as mock_critical:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_critical.assert_called_once_with(
                "Third party error sending to FCM - code"
            )

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

    def test_send_fcm_invalid_argument_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, InvalidArgumentError("code", "message"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response), patch(
            "logging.critical"
        ) as mock_critical:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_critical.assert_called_once_with(
                "Invalid argument when sending to FCM - code"
            )

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        # Make sure we haven't queued for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

    def test_send_fcm_internal_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, InternalError("code", "message"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response), patch(
            "logging.error"
        ) as mock_error:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_error.assert_called_once_with("Interal FCM error - retrying client...")

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        # Check that we queue'd for a retry
        # NOTE: Removed in https://github.com/the-blue-alliance/the-blue-alliance/pull/4620
        # tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        # assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        # with patch.object(TBANSHelper, "_send_fcm") as mock_send_fcm:
        #     deferred.run(tasks[0].payload)
        #     mock_send_fcm.assert_called_once_with([client], ANY, False, 1)

    def test_send_fcm_unavailable_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, UnavailableError("code", "message"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response), patch(
            "logging.error"
        ) as mock_error:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_error.assert_called_once_with("FCM unavailable - retrying client...")

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        # Check that we queue'd for a retry
        # NOTE: Removed in https://github.com/the-blue-alliance/the-blue-alliance/pull/4620
        # tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        # assert len(tasks) == 1

        # Make sure our taskqueue tasks execute what we expect
        # with patch.object(TBANSHelper, "_send_fcm") as mock_send_fcm:
        #     deferred.run(tasks[0].payload)
        #     mock_send_fcm.assert_called_once_with([client], ANY, False, 1)

    def test_send_fcm_unhandled_error(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, FirebaseError("code", "message"))]
        )
        with patch.object(FCMRequest, "send", return_value=batch_response), patch(
            "logging.error"
        ) as mock_error:
            TBANSHelper._send_fcm([client], MockNotification())
            mock_error.assert_called_once_with(
                "Unhandled FCM error for messaging_id - code / message"
            )

        # Sanity check
        assert fcm_messaging_ids("user_id") == ["messaging_id"]

        # Check that we didn't queue for a retry
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 0

    def test_send_fcm_retry_backoff_time(self):
        client = MobileClient(
            parent=ndb.Key(Account, "user_id"),
            user_id="user_id",
            messaging_id="messaging_id",
            client_type=ClientType.OS_IOS,
        )
        client.put()

        # import time

        batch_response = messaging.BatchResponse(
            [messaging.SendResponse(None, QuotaExceededError("code", "message"))]
        )
        for i in range(0, 6):
            with patch.object(FCMRequest, "send", return_value=batch_response), patch(
                "logging.error"
            ):
                # call_time = time.time()
                TBANSHelper._send_fcm([client], MockNotification(), False, i)

                # NOTE: Removed in https://github.com/the-blue-alliance/the-blue-alliance/pull/4620
                # Check that we queue'd for a retry with the proper countdown time
                # tasks = self.taskqueue_stub.get_filtered_tasks(
                #     queue_names="push-notifications"
                # )
                # if i > 0:
                #     assert tasks[0].eta_posix - call_time > 0
                #
                # Make sure our taskqueue tasks execute what we expect
                # with patch.object(TBANSHelper, "_send_fcm") as mock_send_fcm:
                #     deferred.run(tasks[0].payload)
                #     mock_send_fcm.assert_called_once_with([client], ANY, False, i + 1)

                self.taskqueue_stub.FlushQueue("push-notifications")

    def test_send_webhook_disabled(self):
        from backend.common.sitevars.notifications_enable import NotificationsEnable

        NotificationsEnable.enable_notifications(False)

        with patch.object(
            NotificationsEnable,
            "notifications_enabled",
            wraps=NotificationsEnable.notifications_enabled,
        ) as mock_check_enabled:
            TBANSHelper._send_webhook([], MockNotification())
            mock_check_enabled.assert_called_once()

    def test_send_webhook_filter_webhook_clients(self):
        expected = "client_type_{}".format(ClientType.WEBHOOK)
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="client_type_{}".format(client_type),
                client_type=client_type,
            )
            for client_type in CLIENT_TYPE_NAMES.keys()
        ]

        with patch(
            "backend.common.models.notifications.requests.webhook_request.WebhookRequest",
            autospec=True,
        ) as mock_init:
            TBANSHelper._send_webhook(clients, MockNotification())
            mock_init.assert_called_once_with(ANY, expected, ANY)

    def test_send_webhook_filter_webhook_clients_verified(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="unverified",
                client_type=ClientType.WEBHOOK,
                verified=False,
            ),
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="verified",
                client_type=ClientType.WEBHOOK,
                verified=True,
            ),
        ]

        with patch(
            "backend.common.models.notifications.requests.webhook_request.WebhookRequest",
            autospec=True,
        ) as mock_init:
            TBANSHelper._send_webhook(clients, MockNotification())
            mock_init.assert_called_once_with(ANY, "verified", ANY)

    def test_send_webhook_filter_webhook_clients_from_notification(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="unverified",
                client_type=ClientType.WEBHOOK,
                verified=False,
            ),
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="verified",
                client_type=ClientType.WEBHOOK,
                verified=True,
            ),
        ]

        with patch(
            "backend.common.models.notifications.requests.webhook_request.WebhookRequest",
            autospec=True,
        ) as mock_init:
            TBANSHelper._send_webhook(clients, MockNotification(should_send=False))
            mock_init.assert_not_called()

    def test_send_webhook_multiple(self):
        clients = [
            MobileClient(
                parent=ndb.Key(Account, "user_id"),
                user_id="user_id",
                messaging_id="{}".format(i),
                client_type=ClientType.WEBHOOK,
            )
            for i in range(3)
        ]

        batch_response = messaging.BatchResponse([])
        with patch.object(
            WebhookRequest, "send", return_value=batch_response
        ) as mock_send:
            TBANSHelper._send_webhook(clients, MockNotification())
            assert mock_send.call_count == 3

    def test_debug_string(self):
        exception = FirebaseError("code", "message")
        assert TBANSHelper._debug_string(exception) == "code / message"

    def test_debug_string_response(self):
        class MockResponse:
            def json(self):
                import json

                return json.dumps({"mock": "mock"})

        exception = FirebaseError("code", "message", None, MockResponse())
        assert (
            TBANSHelper._debug_string(exception) == 'code / message / {"mock": "mock"}'
        )

    def test_batch_send_subscriptions(self):
        subscriptions = [
            Subscription(
                parent=ndb.Key(Account, f"user_id_{i}"),
                user_id=f"user_id_{i}",
                model_key="frc1",
                model_type=ModelType.TEAM,
                notification_types=[NotificationType.MATCH_SCORE],
            )
            for i in range(750)
        ]
        notification = MockNotification()
        TBANSHelper._batch_send_subscriptions(subscriptions, notification)
        tasks = self.taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
        assert len(tasks) == 2

    def test_send_subscriptions(self):
        subscription = Subscription(
            parent=ndb.Key(Account, "user_id_1"),
            user_id="user_id_1",
            model_key="frc1",
            model_type=ModelType.TEAM,
            notification_types=[NotificationType.MATCH_SCORE],
        )
        notification = MockNotification()
        with patch.object(TBANSHelper, "_send") as mock_send:
            TBANSHelper._send_subscriptions([subscription], notification)
            mock_send.assert_called_once_with(["user_id_1"], notification)
