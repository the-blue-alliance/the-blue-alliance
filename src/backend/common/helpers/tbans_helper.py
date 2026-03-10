import datetime
import enum
import logging
import time

import firebase_admin
from firebase_admin.exceptions import FirebaseError

from backend.common.consts.client_type import (
    ClientType,
    FCM_CLIENTS,
)
from backend.common.consts.notification_type import (
    ENABLED_EVENT_NOTIFICATIONS,
    ENABLED_MATCH_NOTIFICATIONS,
    ENABLED_TEAM_NOTIFICATIONS,
    NotificationType,
)
from backend.common.helpers.deferred import defer_safe
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.alliance_selection import (
    AllianceSelectionNotification,
)
from backend.common.models.notifications.awards import AwardsNotification
from backend.common.models.notifications.district_points import (
    DistrictPointsNotification,
)
from backend.common.models.notifications.event_level import EventLevelNotification
from backend.common.models.notifications.event_schedule import (
    EventScheduleNotification,
)
from backend.common.models.notifications.match_score import MatchScoreNotification
from backend.common.models.notifications.match_upcoming import (
    MatchUpcomingNotification,
)
from backend.common.models.notifications.match_video import MatchVideoNotification
from backend.common.models.notifications.mytba import (
    FavoritesUpdatedNotification,
    SubscriptionsUpdatedNotification,
)
from backend.common.models.notifications.notification import Notification
from backend.common.models.notifications.ping import PingNotification
from backend.common.models.notifications.requests.fcm_request import (
    FCMRequest,
    MAXIMUM_TOKENS,
)
from backend.common.models.notifications.requests.webhook_request import WebhookRequest
from backend.common.models.notifications.verification import VerificationNotification
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team
from backend.common.queries.mobile_client_query import MobileClientQuery

MAXIMUM_BACKOFF = 32
MATCH_UPCOMING_MINUTES = datetime.timedelta(minutes=-7)


class _NotificationMode(enum.Flag):
    """Controls which client types receive a notification.

    Uses Flag so members compose with bitwise OR::

        _NotificationMode.FCM | _NotificationMode.WEBHOOK == _NotificationMode.ALL

    and can be tested with bitwise AND::

        if mode & _NotificationMode.FCM:  # True for FCM and ALL
    """

    FCM = enum.auto()
    WEBHOOK = enum.auto()
    ALL = FCM | WEBHOOK  # pyre-ignore[8]


def _firebase_app():
    from firebase_admin import credentials

    try:
        creds = credentials.Certificate("service-account-key.json")
    except Exception:
        creds = None
    try:
        return firebase_admin.get_app("tbans")
    except ValueError:
        return firebase_admin.initialize_app(creds, name="tbans")


firebase_app = _firebase_app()


class TBANSHelper:
    """
    Helper class for sending push notifications via the FCM HTTPv1 API and sending data payloads to webhooks
    """

    @classmethod
    def alliance_selection(cls, event_key: str) -> None:
        event = Event.get_by_id(event_key)
        if event is None:
            return

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.ALLIANCE_SELECTION in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                event, NotificationType.ALLIANCE_SELECTION
            )

        # Send to Team subscribers
        # Key is a team key, value is a future
        team_subscriptions_futures = {}
        if NotificationType.ALLIANCE_SELECTION in ENABLED_TEAM_NOTIFICATIONS:
            for team_key in event.alliance_teams:
                try:
                    team = Team.get_by_id(team_key)
                except Exception:
                    continue

                team_subscriptions_futures[team_key] = (
                    Subscription.subscriptions_for_team(
                        team, NotificationType.ALLIANCE_SELECTION
                    )
                )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(),
                AllianceSelectionNotification(event),
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(),
                AllianceSelectionNotification(event, team),
            )

    @classmethod
    def awards(
        cls,
        event_key: str,
        new_award_team_keys: set[str],
    ) -> None:
        """Dispatch award notifications.

        Args:
            event_key: The event key string.
            new_award_team_keys: Team key strings from new Award entities in
                this update.
                - non-empty set: send FCM + webhooks for matching teams and
                  at the event level; webhooks only for other teams.
                - empty set: no new awards, only existing awards were updated
                  — send webhooks only so consumers stay in sync.
        """
        event = Event.get_by_id(event_key)
        if event is None:
            return

        # Determine notification mode.
        # non-empty -> new awards exist for those teams, FCM + webhooks
        # empty     -> update-only, webhooks only
        event_mode = (
            _NotificationMode.ALL if new_award_team_keys else _NotificationMode.WEBHOOK
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.AWARDS in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                event, NotificationType.AWARDS
            )
        # Send to Team subscribers
        # Key is a team key, value is a future
        team_subscriptions_futures = {}
        if NotificationType.AWARDS in ENABLED_TEAM_NOTIFICATIONS:
            # Map all Teams to their Awards so we can populate our Awards notification with more specific info
            team_awards = event.team_awards()
            for team_key in team_awards.keys():
                team = team_key.get()
                if not team:
                    continue

                if team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.AWARDS
                        )
                    )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(),
                AwardsNotification(event),
                event_mode,
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            # FCM only for teams with new awards;
            # webhooks always fire so consumers stay in sync.
            if team_key in new_award_team_keys:
                team_mode = _NotificationMode.ALL
            else:
                team_mode = _NotificationMode.WEBHOOK

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(),
                AwardsNotification(event, team),
                team_mode,
            )

    @classmethod
    def event_level(cls, match_key: str) -> None:
        match = Match.get_by_id(match_key)
        if match is None:
            return

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.LEVEL_STARTING in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                match.event.get(), NotificationType.LEVEL_STARTING
            )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(), EventLevelNotification(match)
            )

    @classmethod
    def event_schedule(cls, event_key: str) -> None:
        event = Event.get_by_id(event_key)
        if event is None:
            return

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.SCHEDULE_UPDATED in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                event, NotificationType.SCHEDULE_UPDATED
            )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(),
                EventScheduleNotification(event),
            )

    @classmethod
    def match_score(
        cls,
        match_key: str,
        is_score_breakdown_update: bool = False,
    ) -> None:
        """Dispatch match score notifications.

        Accepts a match key string (not a full Match object) so the
        deferred task payload stays tiny and we always read the latest
        data from Datastore when the task executes.

        Args:
            match_key: The string key name of the Match (e.g. "2024ct_qm1").
            is_score_breakdown_update: When True, this notification is being sent
                because a score breakdown was added to a match whose score was
                already sent. Only webhook clients are notified and upcoming
                match scheduling is skipped.
        """
        match = Match.get_by_id(match_key)
        if match is None:
            return

        if not match.has_been_played:
            return

        event = match.event.get()

        # Score breakdown updates only go to webhooks — mobile clients
        # already received the initial push notification for this match.
        mode = (
            _NotificationMode.WEBHOOK
            if is_score_breakdown_update
            else _NotificationMode.ALL
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.MATCH_SCORE in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                event, NotificationType.MATCH_SCORE
            )

        # Send to Team subscribers
        # Key is a team key, value is a future
        team_subscriptions_futures = {}
        if NotificationType.MATCH_SCORE in ENABLED_TEAM_NOTIFICATIONS:
            for team_key in match.team_keys:
                team = team_key.get()
                if not team:
                    continue

                if team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.MATCH_SCORE
                        )
                    )

        # Send to Match subscribers
        match_subscriptions_future = None
        if NotificationType.MATCH_SCORE in ENABLED_MATCH_NOTIFICATIONS:
            match_subscriptions_future = Subscription.subscriptions_for_match(
                match, NotificationType.MATCH_SCORE
            )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(),
                MatchScoreNotification(match),
                mode,
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(),
                MatchScoreNotification(match, team),
                mode,
            )

        if match_subscriptions_future:
            cls._batch_send_subscriptions(
                match_subscriptions_future.get_result(),
                MatchScoreNotification(match),
                mode,
            )

        # Send UPCOMING_MATCH for the N + 2 match after this one.
        # Skip for score breakdown updates — upcoming match scheduling
        # was already handled by the initial match score notification.
        if is_score_breakdown_update:
            return

        if not event.matches:
            return
        from backend.common.helpers.match_helper import MatchHelper

        next_matches = MatchHelper.upcoming_matches(event.matches, num=2)
        # TODO: Think about if we need special-case handling for replayed matches
        # (I don't think we do because if a match gets replayed at EoD, we'll cancel/reschedule
        # for that match notification. If a match gets replayed back-to-back (which doesn't happen?)
        # sending a second notification is probably fine.
        # Schedule upcoming notifications for all next matches. Normally the
        # 2nd (N+2) is the only new one — having N+1 re-scheduled is harmless
        # (task-name dedup) and covers comp-level boundaries in double-elimination
        # brackets where N+1/N+2 may not have existed when earlier matches scored.
        for match in next_matches:
            cls.schedule_upcoming_match(match.key_name)

    @classmethod
    def match_upcoming(cls, match_key: str) -> None:
        match = Match.get_by_id(match_key)
        if match is None:
            return

        # Guard against duplicate sends — multiple code paths can schedule
        # the same upcoming match (e.g. at comp-level boundaries in double
        # elimination). push_sent is persisted so it survives across tasks.
        if match.push_sent:
            return

        from backend.common.manipulators.match_manipulator import MatchManipulator

        match.push_sent = True
        MatchManipulator.createOrUpdate(match, run_post_update_hook=False)

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.UPCOMING_MATCH in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                match.event.get(), NotificationType.UPCOMING_MATCH
            )

        # Send to Team subscribers
        # Key is a team key, value is a future
        team_subscriptions_futures = {}
        if NotificationType.UPCOMING_MATCH in ENABLED_TEAM_NOTIFICATIONS:
            for team_key in match.team_keys:
                team = team_key.get()
                if not team:
                    continue

                if team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.UPCOMING_MATCH
                        )
                    )

        # Send to Match subscribers
        match_subscriptions_future = None
        if NotificationType.UPCOMING_MATCH in ENABLED_MATCH_NOTIFICATIONS:
            match_subscriptions_future = Subscription.subscriptions_for_match(
                match, NotificationType.UPCOMING_MATCH
            )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(),
                MatchUpcomingNotification(match),
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(),
                MatchUpcomingNotification(match, team),
            )

        if match_subscriptions_future:
            cls._batch_send_subscriptions(
                match_subscriptions_future.get_result(),
                MatchUpcomingNotification(match),
            )

        # Send LEVEL_STARTING for the first match of a new type
        if match.set_number == 1 and match.match_number == 1:
            cls.event_level(match_key)

    @classmethod
    def match_video(cls, match_key: str) -> None:
        match = Match.get_by_id(match_key)
        if match is None:
            return

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.MATCH_VIDEO in ENABLED_EVENT_NOTIFICATIONS:
            event_subscriptions_future = Subscription.subscriptions_for_event(
                match.event.get(), NotificationType.MATCH_VIDEO
            )

        # Send to Team subscribers
        # Key is a team key, value is a future
        team_subscriptions_futures = {}
        if NotificationType.MATCH_VIDEO in ENABLED_TEAM_NOTIFICATIONS:
            for team_key in match.team_keys:
                team = team_key.get()
                if not team:
                    continue

                if team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.MATCH_VIDEO
                        )
                    )

        # Send to Match subscribers
        match_subscriptions_future = None
        if NotificationType.MATCH_VIDEO in ENABLED_MATCH_NOTIFICATIONS:
            match_subscriptions_future = Subscription.subscriptions_for_match(
                match, NotificationType.MATCH_VIDEO
            )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(), MatchVideoNotification(match)
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(),
                MatchVideoNotification(match, team),
            )

        if match_subscriptions_future:
            cls._batch_send_subscriptions(
                match_subscriptions_future.get_result(), MatchVideoNotification(match)
            )

    @classmethod
    def update_favorites(
        cls, user_id: str, initiating_device_id: str | None = None
    ) -> None:
        cls._send(
            [user_id], FavoritesUpdatedNotification(user_id, initiating_device_id)
        )

    @classmethod
    def update_subscriptions(
        cls, user_id: str, initiating_device_id: str | None = None
    ) -> None:
        cls._send(
            [user_id], SubscriptionsUpdatedNotification(user_id, initiating_device_id)
        )

    @staticmethod
    def ping(client: MobileClient) -> tuple[bool, bool]:
        """Immediately dispatch a Ping to either FCM or a webhook"""
        if client.client_type == ClientType.WEBHOOK:
            return TBANSHelper._ping_webhook(client)
        else:
            return TBANSHelper._ping_client(client)

    @staticmethod
    def _ping_client(client: MobileClient) -> tuple[bool, bool]:
        client_type = client.client_type
        if client_type in FCM_CLIENTS:
            notification = PingNotification()

            fcm_request = FCMRequest(
                firebase_app,
                notification,
                tokens=[client.messaging_id],
            )

            batch_response = fcm_request.send()
            if batch_response.failure_count > 0:
                return (False, False)
        else:
            raise Exception("Unsupported FCM client type: {}".format(client_type))

        return (True, True)

    @staticmethod
    def _ping_webhook(client: MobileClient) -> tuple[bool, bool]:
        notification = PingNotification()

        webhook_request = WebhookRequest(
            notification, client.messaging_id, client.secret
        )

        return webhook_request.send()

    @classmethod
    def schedule_upcoming_match(cls, match_key: str) -> None:
        match = Match.get_by_id(match_key)
        if match is None:
            return

        now = datetime.datetime.now(datetime.timezone.utc).replace(  # pyre-ignore[16]
            tzinfo=None
        )

        task_name = f"{match_key}_match_upcoming_{int(now.timestamp())}"

        if match.time is not None and match.time + MATCH_UPCOMING_MINUTES > now:
            eta = match.time + MATCH_UPCOMING_MINUTES
        else:
            eta = now

        try:
            defer_safe(
                cls.match_upcoming,
                match_key,
                _name=task_name,
                _target="py3-tasks-io",
                _queue="push-notifications",
                _url="/_ah/queue/deferred_notification_send",
                _eta=eta,
            )
        except Exception:
            pass

    @classmethod
    def schedule_upcoming_matches(cls, event_key: str) -> None:
        event = Event.get_by_id(event_key)
        if event is None:
            return

        # Schedule `match_upcoming` notifications for Match 1 and Match 2
        # Match 3 (and onward) will be dispatched after Match 1 (or Match N - 2) has been played
        if not event.matches:
            return

        from backend.common.helpers.match_helper import MatchHelper

        next_matches = MatchHelper.upcoming_matches(event.matches, num=2)

        if len(next_matches) == 0:
            return

        # Only schedule/send upcoming matches for new levels - if a schedule gets updated mid-way through the event, don't
        # bother sending new notifications (this is to prevent a bug where we send a bunch of duplicate notifications)
        if not (next_matches[0].set_number == 1 and next_matches[0].match_number == 1):
            return

        for match in next_matches:
            cls.schedule_upcoming_match(match.key_name)

    @staticmethod
    def verify_webhook(url: str, secret: str) -> str:
        """Immediately dispatch a Verification to a webhook"""
        notification = VerificationNotification(url, secret)

        webhook_request = WebhookRequest(notification, url, secret)
        webhook_request.send()

        return notification.verification_key

    @staticmethod
    def send_webhook_test(
        client: MobileClient,
        notification_type: NotificationType,
        event_key: str | None = None,
        team_key: str | None = None,
        match_key: str | None = None,
        district_key: str | None = None,
    ) -> bool:
        """
        Send a single test notification directly to a specific webhook.

        This method is used for webhook testing from the API docs page to send
        exactly one notification to exactly one webhook, avoiding the issues with
        the normal dispatch flow which sends to all devices and multiple notification
        variants.

        Args:
            client: The MobileClient webhook to send to (must be a verified webhook)
            notification_type: The type of notification to send
            event_key: The event key (required for event-based notifications)
            team_key: The team key (optional, for team-specific notifications)
            match_key: The match key (required for match-based notifications)
            district_key: The district key (required for district-based notifications)

        Returns:
            True if the notification was sent successfully, False otherwise
        """
        # Only send to verified webhook clients
        if client.client_type != ClientType.WEBHOOK:
            return False

        if not client.verified:
            return False

        # Create the notification based on type
        notification = TBANSHelper._create_test_notification(
            notification_type,
            event_key=event_key,
            team_key=team_key,
            match_key=match_key,
            district_key=district_key,
        )
        if notification is None:
            return False

        webhook_request = WebhookRequest(
            notification, client.messaging_id, client.secret
        )
        success, _ = webhook_request.send()

        return success

    @staticmethod
    def _create_test_notification(
        notification_type: NotificationType,
        event_key: str | None = None,
        team_key: str | None = None,
        match_key: str | None = None,
        district_key: str | None = None,
    ) -> Notification | None:
        """
        Create a single notification instance for testing.

        Returns None if required keys are missing or entities not found.
        """
        event = None
        if event_key:
            event = Event.get_by_id(event_key)

        team = None
        if team_key:
            team = Team.get_by_id(team_key)

        match = None
        if match_key:
            match = Match.get_by_id(match_key)

        district = None
        if district_key:
            district = District.get_by_id(district_key)

        if notification_type == NotificationType.ALLIANCE_SELECTION:
            if event is None:
                return None
            return (
                AllianceSelectionNotification(event, team)
                if team
                else AllianceSelectionNotification(event)
            )

        elif notification_type == NotificationType.AWARDS:
            if event is None:
                return None
            return (
                AwardsNotification(event, team) if team else AwardsNotification(event)
            )

        elif notification_type == NotificationType.DISTRICT_POINTS_UPDATED:
            if district is None:
                return None
            return DistrictPointsNotification(district)

        elif notification_type == NotificationType.LEVEL_STARTING:
            if match is None:
                return None
            return EventLevelNotification(match)

        elif notification_type == NotificationType.MATCH_SCORE:
            if match is None:
                return None
            return (
                MatchScoreNotification(match, team)
                if team
                else MatchScoreNotification(match)
            )

        elif notification_type == NotificationType.UPCOMING_MATCH:
            if match is None:
                return None
            return (
                MatchUpcomingNotification(match, team)
                if team
                else MatchUpcomingNotification(match)
            )

        elif notification_type == NotificationType.MATCH_VIDEO:
            if match is None:
                return None
            return (
                MatchVideoNotification(match, team)
                if team
                else MatchVideoNotification(match)
            )

        elif notification_type == NotificationType.PING:
            return PingNotification()

        elif notification_type == NotificationType.SCHEDULE_UPDATED:
            if event is None:
                return None
            return (
                EventScheduleNotification(event, match)
                if match
                else EventScheduleNotification(event)
            )

        return None

    @classmethod
    def _batch_send_subscriptions(
        cls,
        subscriptions: list[Subscription],
        notification: Notification,
        mode: _NotificationMode = _NotificationMode.ALL,
    ) -> None:
        def batch(iterable, n=1):
            la = len(iterable)
            for ndx in range(0, la, n):
                yield iterable[ndx : min(ndx + n, la)]

        BATCH_SIZE = 500

        for batch in batch(subscriptions, BATCH_SIZE):
            defer_safe(
                cls._send_subscriptions,
                batch,
                notification,
                mode,
                _target="py3-tasks-io",
                _queue="push-notifications",
                _url="/_ah/queue/deferred_notification_send",
            )

    @classmethod
    def _send_subscriptions(
        cls,
        subscriptions: list[Subscription],
        notification: Notification,
        mode: _NotificationMode = _NotificationMode.ALL,
    ) -> None:
        # Convert subscriptions -> user IDs
        # Allows us to send in batches
        users = list(set([sub.user_id for sub in subscriptions]))
        cls._send(users, notification, mode)

    @classmethod
    def _send(
        cls,
        user_ids: list[str],
        notification: Notification,
        mode: _NotificationMode = _NotificationMode.ALL,
    ) -> None:
        send_fcm = bool(mode & _NotificationMode.FCM)
        send_webhooks = bool(mode & _NotificationMode.WEBHOOK)

        fcm_clients_future = (
            MobileClientQuery(user_ids, client_types=list(FCM_CLIENTS)).fetch_async()
            if send_fcm
            else None
        )
        webhook_clients_future = (
            MobileClientQuery(user_ids, client_types=[ClientType.WEBHOOK]).fetch_async()
            if send_webhooks
            else None
        )

        # Send to FCM clients
        if fcm_clients_future:
            fcm_clients = fcm_clients_future.get_result()
            if fcm_clients:
                cls._defer_fcm(fcm_clients, notification)

        # Send to webhooks
        if webhook_clients_future:
            webhook_clients = webhook_clients_future.get_result()
            if webhook_clients:
                for webhook in webhook_clients:
                    cls._defer_webhook(webhook, notification)

    @classmethod
    def _defer_fcm(
        cls, clients: list[MobileClient], notification: Notification
    ) -> None:
        defer_safe(
            cls._send_fcm,
            clients,
            notification,
            _target="py3-tasks-io",
            _queue="push-notifications",
            _url="/_ah/queue/deferred_notification_send",
        )

    @classmethod
    def _defer_webhook(cls, clients: MobileClient, notification: Notification) -> None:
        defer_safe(
            cls._send_webhook,
            clients,
            notification,
            _target="py3-tasks-io",
            _queue="push-notifications",
            _url="/_ah/queue/deferred_notification_send",
        )

    @classmethod
    def _send_fcm(
        cls,
        clients: list[MobileClient],
        notification: Notification,
        backoff_iteration: int = 0,
    ) -> None:
        # Only send to FCM clients if notifications are enabled
        if not cls._notifications_enabled():
            return

        # Only allow so many retries
        backoff_time = 2**backoff_iteration
        if backoff_time > MAXIMUM_BACKOFF:
            return

        # Make sure we're only sending to FCM clients
        clients = [
            client
            for client in clients
            if client.client_type in FCM_CLIENTS
            and notification.should_send_to_client(client)
        ]

        # We can only send to so many FCM clients at a time - send to our clients across several requests
        for subclients in [
            clients[i : i + MAXIMUM_TOKENS]
            for i in range(0, len(clients), MAXIMUM_TOKENS)
        ]:
            fcm_request = FCMRequest(
                firebase_app,
                notification,
                tokens=[client.messaging_id for client in subclients],
            )

            logging.info(f"Sending FCM request: {time.strftime('%X')}")
            batch_response = fcm_request.send()
            logging.info(f"Got FCM response: {time.strftime('%X')}")
            retry_clients = []

            # Handle our failed sends - this might include logging/alerting, removing old clients, or retrying sends
            from firebase_admin.exceptions import (
                InvalidArgumentError,
                InternalError,
                UnavailableError,
            )
            from firebase_admin.messaging import (
                QuotaExceededError,
                SenderIdMismatchError,
                ThirdPartyAuthError,
                UnregisteredError,
            )

            for index, response in enumerate(batch_response.responses):
                if response.success:
                    continue
                client = subclients[index]
                if isinstance(response.exception, UnregisteredError):
                    logging.info(
                        f"Deleting mobile client with ID: {client.messaging_id}"
                    )
                    MobileClientQuery.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, SenderIdMismatchError):
                    logging.info(
                        f"Deleting mobile client with ID: {client.messaging_id}"
                    )
                    MobileClientQuery.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, QuotaExceededError):
                    logging.error("Quota exceeded - retrying client...")
                    retry_clients.append(client)
                elif isinstance(response.exception, ThirdPartyAuthError):
                    logging.critical(
                        "Third party error sending to FCM - {}".format(
                            response.exception
                        )
                    )
                elif isinstance(response.exception, InvalidArgumentError):
                    logging.critical(
                        "Invalid argument when sending to FCM - {}".format(
                            response.exception
                        )
                    )
                elif isinstance(response.exception, InternalError):
                    logging.error("Internal FCM error - retrying client...")
                    retry_clients.append(client)
                elif isinstance(response.exception, UnavailableError):
                    logging.error("FCM unavailable - retrying client...")
                    retry_clients.append(client)
                else:
                    debug_string = cls._debug_string(response.exception)
                    logging.error(
                        "Unhandled FCM error for {} - {}".format(
                            client.messaging_id, debug_string
                        )
                    )

            # if retry_clients:
            #     # Try again, with exponential backoff
            #     defer_safe(
            #         cls._send_fcm,
            #         retry_clients,
            #         notification,
            #         backoff_iteration + 1,
            #         _countdown=backoff_time,
            #         _target="py3-tasks-io",
            #         _queue="push-notifications",
            #         _url="/_ah/queue/deferred_notification_send",
            #     )

        return

    @classmethod
    def _send_webhook(cls, client: MobileClient, notification: Notification) -> None:
        # Only send to webhooks if notifications are enabled
        if not cls._notifications_enabled():
            return

        # Make sure we're only sending to verified webhook clients
        if client.client_type != ClientType.WEBHOOK or not client.verified:
            return

        if not notification.should_send_to_client(client):
            return

        webhook_request = WebhookRequest(
            notification, client.messaging_id, client.secret
        )
        webhook_request.send()

        return

    # Returns a list of debug strings for a FirebaseError
    @classmethod
    def _debug_string(cls, exception: FirebaseError) -> str:
        debug_strings = [exception.code, str(exception)]
        if exception.http_response:
            debug_strings.append(str(exception.http_response.json()))
        return " / ".join(debug_strings)

    @classmethod
    def _notifications_enabled(cls) -> bool:
        from backend.common.sitevars.notifications_enable import NotificationsEnable

        return NotificationsEnable.notifications_enabled()
