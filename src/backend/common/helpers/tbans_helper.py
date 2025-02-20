import datetime
import logging
import time
from typing import List, Optional

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
from backend.common.memcache import MemcacheClient
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.notification import Notification
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team
from backend.common.queries.mobile_client_query import MobileClientQuery


MAXIMUM_BACKOFF = 32
MATCH_UPCOMING_MINUTES = datetime.timedelta(minutes=-7)


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

    @staticmethod
    def _format_tbans_memcache_key(key: str) -> bytes:
        return f"tbans_{key}".encode()

    @staticmethod
    def _has_sent_notification(key: str) -> bool:
        key = TBANSHelper._format_tbans_memcache_key(key)

        memcache = MemcacheClient.get()
        has_sent_notification: Optional[bool] = memcache.get(key)
        if has_sent_notification is None:
            return False
        return has_sent_notification

    @staticmethod
    def _set_has_sent_notification(key: str, time_seconds: int = 60 * 60) -> None:
        key = TBANSHelper._format_tbans_memcache_key(key)

        memcache = MemcacheClient.get()
        memcache.set(key, True, time_seconds)

    @classmethod
    def alliance_selection(cls, event: Event, user_id: Optional[str] = None) -> None:
        memcache_key = f"{event.key_name}_alliance_selection"
        # Always send if we're passing an individual user_id
        if user_id is None and TBANSHelper._has_sent_notification(memcache_key):
            return

        from backend.common.models.notifications.alliance_selection import (
            AllianceSelectionNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.ALLIANCE_SELECTION in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], AllianceSelectionNotification(event))
            else:
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

                if user_id:
                    cls._send([user_id], AllianceSelectionNotification(event, team))
                else:
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

        if not user_id:
            TBANSHelper._set_has_sent_notification(memcache_key)

    """
    Dispatch Awards notifications to users subscribed to Event or Team Award notifications.

    Args:
        event (models.event.Event): The Event to query Subscriptions for.
        user_id (string): A user ID to only send notifications for - used ONLY for TBANS Admin testing.

    Returns:
        list (string): List of user IDs with Subscriptions to the given Event/notification type.
    """

    @classmethod
    def awards(cls, event: Event, user_id: Optional[str] = None) -> None:
        memcache_key = f"{event.key_name}_awards"
        # Always send if we're passing an individual user_id
        if user_id is None and TBANSHelper._has_sent_notification(memcache_key):
            return

        from backend.common.models.notifications.awards import (
            AwardsNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.AWARDS in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], AwardsNotification(event))
            else:
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

                if user_id:
                    cls._send([user_id], AwardsNotification(event, team))
                elif team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.AWARDS
                        )
                    )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(), AwardsNotification(event)
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(), AwardsNotification(event, team)
            )

        if not user_id:
            TBANSHelper._set_has_sent_notification(memcache_key)

    @classmethod
    def broadcast(
        cls,
        client_types: List[ClientType],
        title: str,
        message: str,
        url: Optional[str] = None,
        app_version: Optional[str] = None,
    ):
        from backend.common.models.notifications.broadcast import (
            BroadcastNotification,
        )

        notification = BroadcastNotification(title, message, url, app_version)

        # Send to FCM clients
        fcm_client_types = [ct for ct in client_types if ct in FCM_CLIENTS]
        if fcm_client_types:
            clients = MobileClient.query(
                MobileClient.client_type.IN(fcm_client_types)
            ).fetch()
            if clients:
                cls._defer_fcm(clients, notification)

        # Send to webhooks
        if ClientType.WEBHOOK in client_types:
            clients = MobileClient.query(
                MobileClient.client_type == ClientType.WEBHOOK
            ).fetch()
            if clients:
                cls._defer_webhook(clients, notification)

    @classmethod
    def event_level(cls, match: Match, user_id: Optional[str] = None) -> None:
        event = match.event.get()

        memcache_key = f"{match.key_name}_event_level"
        # Always send if we're passing an individual user_id
        if user_id is None and TBANSHelper._has_sent_notification(memcache_key):
            return

        from backend.common.models.notifications.event_level import (
            EventLevelNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.LEVEL_STARTING in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], EventLevelNotification(match))
            else:
                event_subscriptions_future = Subscription.subscriptions_for_event(
                    match.event.get(), NotificationType.LEVEL_STARTING
                )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(), EventLevelNotification(match)
            )

        if not user_id:
            TBANSHelper._set_has_sent_notification(memcache_key)

    @classmethod
    def event_schedule(cls, event: Event, user_id: Optional[str] = None) -> None:
        memcache_key = f"{event.key_name}_event_schedule"
        # Always send if we're passing an individual user_id
        if user_id is None and TBANSHelper._has_sent_notification(memcache_key):
            return

        from backend.common.models.notifications.event_schedule import (
            EventScheduleNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.SCHEDULE_UPDATED in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], EventScheduleNotification(event))
            else:
                event_subscriptions_future = Subscription.subscriptions_for_event(
                    event, NotificationType.SCHEDULE_UPDATED
                )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(),
                EventScheduleNotification(event),
            )

        if not user_id:
            TBANSHelper._set_has_sent_notification(memcache_key)

    @classmethod
    def match_score(cls, match: Match, user_id: Optional[str] = None) -> None:
        memcache_key = f"{match.key_name}_match_score"
        # Always send if we're passing an individual user_id
        if user_id is None and TBANSHelper._has_sent_notification(memcache_key):
            return

        event = match.event.get()

        from backend.common.models.notifications.match_score import (
            MatchScoreNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.MATCH_SCORE in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], MatchScoreNotification(match))
            else:
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

                if user_id:
                    cls._send([user_id], MatchScoreNotification(match, team))
                elif team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.MATCH_SCORE
                        )
                    )

        # Send to Match subscribers
        match_subscriptions_future = None
        if NotificationType.MATCH_SCORE in ENABLED_MATCH_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], MatchScoreNotification(match))
            else:
                match_subscriptions_future = Subscription.subscriptions_for_match(
                    match, NotificationType.MATCH_SCORE
                )

        if event_subscriptions_future:
            cls._batch_send_subscriptions(
                event_subscriptions_future.get_result(), MatchScoreNotification(match)
            )

        for team_key, team_subscriptions_future in team_subscriptions_futures.items():
            try:
                team = Team.get_by_id(team_key)
            except Exception:
                continue

            cls._batch_send_subscriptions(
                team_subscriptions_future.get_result(),
                MatchScoreNotification(match, team),
            )

        if match_subscriptions_future:
            cls._batch_send_subscriptions(
                match_subscriptions_future.get_result(), MatchScoreNotification(match)
            )

        if not user_id:
            TBANSHelper._set_has_sent_notification(memcache_key)

        # Send UPCOMING_MATCH for the N + 2 match after this one
        if not event.matches:
            return
        from backend.common.helpers.match_helper import MatchHelper

        next_matches = MatchHelper.upcoming_matches(event.matches, num=2)
        # TODO: Think about if we need special-case handling for replayed matches
        # (I don't think we do because if a match gets replayed at EoD, we'll cancel/reschedule
        # for that match notification. If a match gets replayed back-to-back (which doesn't happen?)
        # sending a second notification is probably fine.
        # If there are not 2 scheduled matches (end of Quals, end of Quarters, etc.) don't send
        if len(next_matches) < 2:
            return

        next_match = next_matches.pop()
        cls.schedule_upcoming_match(next_match, user_id)

    @classmethod
    def match_upcoming(cls, match: Match, user_id: Optional[str] = None) -> None:
        memcache_key = f"{match.key_name}_match_upcoming"
        # Always send if we're passing an individual user_id
        if user_id is None and TBANSHelper._has_sent_notification(memcache_key):
            return

        from backend.common.models.notifications.match_upcoming import (
            MatchUpcomingNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.UPCOMING_MATCH in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], MatchUpcomingNotification(match))
            else:
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

                if user_id:
                    cls._send([user_id], MatchUpcomingNotification(match, team))
                elif team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.UPCOMING_MATCH
                        )
                    )

        # Send to Match subscribers
        match_subscriptions_future = None
        if NotificationType.UPCOMING_MATCH in ENABLED_MATCH_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], MatchUpcomingNotification(match))
            else:
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

        if not user_id:
            TBANSHelper._set_has_sent_notification(memcache_key)

        # Send LEVEL_STARTING for the first match of a new type
        if match.set_number == 1 and match.match_number == 1:
            cls.event_level(match, user_id)

    @classmethod
    def match_video(cls, match: Match, user_id: Optional[str] = None) -> None:
        from backend.common.models.notifications.match_video import (
            MatchVideoNotification,
        )

        # Send to Event subscribers
        event_subscriptions_future = None
        if NotificationType.MATCH_VIDEO in ENABLED_EVENT_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], MatchVideoNotification(match))
            else:
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

                if user_id:
                    cls._send([user_id], MatchVideoNotification(match, team))
                elif team.key_name:
                    team_subscriptions_futures[team.key_name] = (
                        Subscription.subscriptions_for_team(
                            team, NotificationType.MATCH_VIDEO
                        )
                    )

        # Send to Match subscribers
        match_subscriptions_future = None
        if NotificationType.MATCH_VIDEO in ENABLED_MATCH_NOTIFICATIONS:
            if user_id:
                cls._send([user_id], MatchVideoNotification(match))
            else:
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
        cls, user_id: str, initiating_device_id: Optional[str] = None
    ) -> None:
        from backend.common.models.notifications.mytba import (
            FavoritesUpdatedNotification,
        )

        cls._send(
            [user_id], FavoritesUpdatedNotification(user_id, initiating_device_id)
        )

    @classmethod
    def update_subscriptions(
        cls, user_id: str, initiating_device_id: Optional[str] = None
    ) -> None:
        from backend.common.models.notifications.mytba import (
            SubscriptionsUpdatedNotification,
        )

        cls._send(
            [user_id], SubscriptionsUpdatedNotification(user_id, initiating_device_id)
        )

    @staticmethod
    def ping(client: MobileClient) -> bool:
        """Immediately dispatch a Ping to either FCM or a webhook"""
        if client.client_type == ClientType.WEBHOOK:
            return TBANSHelper._ping_webhook(client)
        else:
            return TBANSHelper._ping_client(client)

    @staticmethod
    def _ping_client(client: MobileClient) -> bool:
        client_type = client.client_type
        if client_type in FCM_CLIENTS:
            from backend.common.models.notifications.ping import (
                PingNotification,
            )

            notification = PingNotification()

            from backend.common.models.notifications.requests.fcm_request import (
                FCMRequest,
            )

            fcm_request = FCMRequest(
                firebase_app,
                notification,
                tokens=[client.messaging_id],
            )

            batch_response = fcm_request.send()
            if batch_response.failure_count > 0:
                return False
        else:
            raise Exception("Unsupported FCM client type: {}".format(client_type))

        return True

    @staticmethod
    def _ping_webhook(client: MobileClient) -> bool:
        from backend.common.models.notifications.ping import PingNotification

        notification = PingNotification()

        from backend.common.models.notifications.requests.webhook_request import (
            WebhookRequest,
        )

        webhook_request = WebhookRequest(
            notification, client.messaging_id, client.secret
        )

        return webhook_request.send()

    @classmethod
    def schedule_upcoming_match(
        cls, match: Match, user_id: Optional[str] = None
    ) -> None:
        from google.appengine.api import taskqueue

        queue = taskqueue.Queue("push-notifications")

        if not match.key_name:
            return

        task_name = "{}_match_upcoming".format(match.key_name)
        # Cancel any previously-scheduled `match_upcoming` notifications for this match
        queue.delete_tasks(taskqueue.Task(name=task_name))

        now = datetime.datetime.now(datetime.timezone.utc).replace(  # pyre-ignore[16]
            tzinfo=None
        )
        # If we know when our match is starting, schedule to send Xmins before start of match.
        # Otherwise, send immediately.
        if match.time is None or match.time + MATCH_UPCOMING_MINUTES <= now:
            cls.match_upcoming(match, user_id)
        else:
            try:
                defer_safe(
                    cls.match_upcoming,
                    match,
                    user_id,
                    _name=task_name,
                    _target="py3-tasks-io",
                    _queue="push-notifications",
                    _url="/_ah/queue/deferred_notification_send",
                    _eta=match.time + MATCH_UPCOMING_MINUTES,
                )
            except Exception:
                pass

    @classmethod
    def schedule_upcoming_matches(
        cls, event: Event, user_id: Optional[str] = None
    ) -> None:
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
            cls.schedule_upcoming_match(match, user_id)

    @staticmethod
    def verify_webhook(url: str, secret: str) -> str:
        """Immediately dispatch a Verification to a webhook"""
        from backend.common.models.notifications.verification import (
            VerificationNotification,
        )

        notification = VerificationNotification(url, secret)

        from backend.common.models.notifications.requests.webhook_request import (
            WebhookRequest,
        )

        webhook_request = WebhookRequest(notification, url, secret)
        webhook_request.send()

        return notification.verification_key

    @classmethod
    def _batch_send_subscriptions(
        cls, subscriptions: List[Subscription], notification: Notification
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
                _target="py3-tasks-io",
                _queue="push-notifications",
                _url="/_ah/queue/deferred_notification_send",
            )

    @classmethod
    def _send_subscriptions(
        cls, subscriptions: List[Subscription], notification: Notification
    ) -> None:
        # Convert subscriptions -> user IDs
        # Allows us to send in batches
        users = list(set([sub.user_id for sub in subscriptions]))
        cls._send(users, notification)

    @classmethod
    def _send(cls, user_ids: List[str], notification: Notification) -> None:
        fcm_clients_future = MobileClientQuery(
            user_ids, client_types=list(FCM_CLIENTS)
        ).fetch_async()
        webhook_clients_future = MobileClientQuery(
            user_ids, client_types=[ClientType.WEBHOOK]
        ).fetch_async()

        # Send to FCM clients
        fcm_clients = fcm_clients_future.get_result()
        if fcm_clients:
            cls._defer_fcm(fcm_clients, notification)

        # Send to webhooks
        webhook_clients = webhook_clients_future.get_result()
        if webhook_clients:
            cls._defer_webhook(webhook_clients, notification)

        if not only_webhooks:
            fcm_clients_future = MobileClientQuery(
                user_ids, client_types=list(FCM_CLIENTS)
            ).fetch_async()
            legacy_fcm_clients_future = MobileClientQuery(
                user_ids, client_types=list(FCM_LEGACY_CLIENTS)
            ).fetch_async()

            # Send to FCM clients
            fcm_clients = fcm_clients_future.get_result()
            if fcm_clients:
                cls._defer_fcm(fcm_clients, notification)

            # Send to Android clients
            # These use the webhook data format, but over FCM
            legacy_fcm_clients = legacy_fcm_clients_future.get_result()
            if legacy_fcm_clients:
                cls._defer_fcm(
                    legacy_fcm_clients, notification, legacy_data_format=True
                )

    @classmethod
    def _defer_fcm(
        cls, clients: List[MobileClient], notification: Notification
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
    def _defer_webhook(
        cls, clients: List[MobileClient], notification: Notification
    ) -> None:
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
        clients: List[MobileClient],
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

        from backend.common.models.notifications.requests.fcm_request import (
            FCMRequest,
            MAXIMUM_TOKENS,
        )

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

            for index, response in enumerate(
                [
                    response
                    for response in batch_response.responses
                    if not response.success
                ]
            ):
                client = subclients[index]
                if isinstance(response.exception, UnregisteredError):
                    logging.info(
                        f"Deleting mobile client with ID: f{client.messaging_id}"
                    )
                    MobileClientQuery.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, SenderIdMismatchError):
                    logging.info(
                        f"Deleting mobile client with ID: f{client.messaging_id}"
                    )
                    MobileClientQuery.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, QuotaExceededError):
                    logging.error("Qutoa exceeded - retrying client...")
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
                    logging.error("Interal FCM error - retrying client...")
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
    def _send_webhook(
        cls, clients: List[MobileClient], notification: Notification
    ) -> None:
        # Only send to webhooks if notifications are enabled
        if not cls._notifications_enabled():
            return

        # Make sure we're only sending to webhook clients
        clients = [
            client
            for client in clients
            if client.client_type == ClientType.WEBHOOK
            and client.verified
            and notification.should_send_to_client(client)
        ]

        from backend.common.models.notifications.requests.webhook_request import (
            WebhookRequest,
        )

        for client in clients:
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
