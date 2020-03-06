import datetime
import firebase_admin
import logging

from consts.client_type import ClientType
from consts.notification_type import NotificationType

from google.appengine.ext import deferred

from models.team import Team
from models.mobile_client import MobileClient
from models.subscription import Subscription


MAXIMUM_BACKOFF = 32
MATCH_UPCOMING_MINUTES = datetime.timedelta(minutes=-7)


def _firebase_app():
    from firebase_admin import credentials
    try:
        creds = credentials.Certificate('service-account-key.json')
    except:
        creds = None
    try:
        return firebase_admin.get_app('tbans')
    except ValueError:
        return firebase_admin.initialize_app(creds, name='tbans')


firebase_app = _firebase_app()


class TBANSHelper:

    """
    Helper class for sending push notifications via the FCM HTTPv1 API and sending data payloads to webhooks
    """

    @classmethod
    def alliance_selection(cls, event, user_id=None):
        from models.notifications.alliance_selection import AllianceSelectionNotification
        # Send to Event subscribers
        if NotificationType.ALLIANCE_SELECTION in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(event, NotificationType.ALLIANCE_SELECTION)
            if users:
                cls._send(users, AllianceSelectionNotification(event))

        # Send to Team subscribers
        if NotificationType.ALLIANCE_SELECTION in NotificationType.enabled_team_notifications:
            for team_key in event.alliance_teams:
                try:
                    team = Team.get_by_id(team_key)
                except:
                    continue

                users = [user_id] if user_id else []
                if not users:
                    users = Subscription.users_subscribed_to_team(team, NotificationType.ALLIANCE_SELECTION)
                if users:
                    cls._send(users, AllianceSelectionNotification(event, team))

    """
    Dispatch Awards notifications to users subscribed to Event or Team Award notifications.

    Args:
        event (models.event.Event): The Event to query Subscriptions for.
        user_id (string): A user ID to only send notifications for - used ONLY for TBANS Admin testing.

    Returns:
        list (string): List of user IDs with Subscriptions to the given Event/notification type.
    """
    @classmethod
    def awards(cls, event, user_id=None):
        from models.notifications.awards import AwardsNotification
        # Send to Event subscribers
        if NotificationType.AWARDS in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(event, NotificationType.AWARDS)
            if users:
                cls._send(users, AwardsNotification(event))

        # Send to Team subscribers
        if NotificationType.AWARDS in NotificationType.enabled_team_notifications:
            # Map all Teams to their Awards so we can populate our Awards notification with more specific info
            team_awards = event.team_awards()
            for team_key in team_awards.keys():
                team = team_key.get()

                users = [user_id] if user_id else []
                if not users:
                    users = Subscription.users_subscribed_to_team(team, NotificationType.AWARDS)
                if users:
                    cls._send(users, AwardsNotification(event, team))

    @classmethod
    def broadcast(cls, client_types, title, message, url=None, app_version=None):
        from models.notifications.broadcast import BroadcastNotification
        notification = BroadcastNotification(title, message, url, app_version)

        # Send to FCM clients
        fcm_client_types = [ct for ct in client_types if ct in ClientType.FCM_CLIENTS]
        if fcm_client_types:
            clients = MobileClient.query(MobileClient.client_type.IN(fcm_client_types)).fetch()
            if clients:
                cls._defer_fcm(clients, notification)

        # Send to webhooks
        if ClientType.WEBHOOK in client_types:
            clients = MobileClient.query(MobileClient.client_type == ClientType.WEBHOOK).fetch()
            if clients:
                cls._defer_webhook(clients, notification)

        if ClientType.OS_ANDROID in client_types:
            clients = MobileClient.query(MobileClient.client_type == ClientType.OS_ANDROID).fetch()
            from helpers.push_helper import PushHelper
            keys = PushHelper.get_client_ids_for_clients(clients)

            from notifications.broadcast import BroadcastNotification
            notification = BroadcastNotification(title, message, url, app_version)
            notification.send(keys)

    @classmethod
    def event_level(cls, match, user_id=None):
        from models.notifications.event_level import EventLevelNotification
        # Send to Event subscribers
        if NotificationType.LEVEL_STARTING in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(match.event.get(), NotificationType.LEVEL_STARTING)
            if users:
                cls._send(users, EventLevelNotification(match))

    @classmethod
    def event_schedule(cls, event, user_id=None):
        from models.notifications.event_schedule import EventScheduleNotification
        # Send to Event subscribers
        if NotificationType.SCHEDULE_UPDATED in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(event, NotificationType.SCHEDULE_UPDATED)
            if users:
                cls._send(users, EventScheduleNotification(event))

    @classmethod
    def match_score(cls, match, user_id=None):
        event = match.event.get()

        from models.notifications.match_score import MatchScoreNotification
        # Send to Event subscribers
        if NotificationType.MATCH_SCORE in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(event, NotificationType.MATCH_SCORE)
            if users:
                cls._send(users, MatchScoreNotification(match))

        # Send to Team subscribers
        if NotificationType.MATCH_SCORE in NotificationType.enabled_team_notifications:
            for team_key in match.team_keys:
                users = [user_id] if user_id else []
                if not users:
                    users = Subscription.users_subscribed_to_team(team_key.get(), NotificationType.MATCH_SCORE)
                if users:
                    cls._send(users, MatchScoreNotification(match, team_key.get()))

        # Send to Match subscribers
        if NotificationType.MATCH_SCORE in NotificationType.enabled_match_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_match(match, NotificationType.MATCH_SCORE)
            if users:
                cls._send(users, MatchScoreNotification(match))

        # Send UPCOMING_MATCH for the N + 2 match after this one
        if not event.matches:
            return
        from helpers.match_helper import MatchHelper
        next_matches = MatchHelper.upcomingMatches(event.matches, num=2)
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
    def match_upcoming(cls, match, user_id=None):
        from models.notifications.match_upcoming import MatchUpcomingNotification
        # Send to Event subscribers
        if NotificationType.UPCOMING_MATCH in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(match.event.get(), NotificationType.UPCOMING_MATCH)
            if users:
                cls._send(users, MatchUpcomingNotification(match))

        # Send to Team subscribers
        if NotificationType.UPCOMING_MATCH in NotificationType.enabled_team_notifications:
            for team_key in match.team_keys:
                users = [user_id] if user_id else []
                if not users:
                    users = Subscription.users_subscribed_to_team(team_key.get(), NotificationType.UPCOMING_MATCH)
                if users:
                    cls._send(users, MatchUpcomingNotification(match, team_key.get()))

        # Send to Match subscribers
        if NotificationType.UPCOMING_MATCH in NotificationType.enabled_match_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_match(match, NotificationType.UPCOMING_MATCH)
            if users:
                cls._send(users, MatchUpcomingNotification(match))

        # Send LEVEL_STARTING for the first match of a new type
        if match.set_number == 1 and match.match_number == 1:
            cls.event_level(match, user_id)

    @classmethod
    def match_video(cls, match, user_id=None):
        from models.notifications.match_video import MatchVideoNotification
        # Send to Event subscribers
        if NotificationType.MATCH_VIDEO in NotificationType.enabled_event_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_event(match.event.get(), NotificationType.MATCH_VIDEO)
            if users:
                cls._send(users, MatchVideoNotification(match))

        # Send to Team subscribers
        if NotificationType.MATCH_VIDEO in NotificationType.enabled_team_notifications:
            for team_key in match.team_keys:
                users = [user_id] if user_id else []
                if not users:
                    users = Subscription.users_subscribed_to_team(team_key.get(), NotificationType.MATCH_VIDEO)
                if users:
                    cls._send(users, MatchVideoNotification(match, team_key.get()))

        # Send to Match subscribers
        if NotificationType.MATCH_VIDEO in NotificationType.enabled_match_notifications:
            users = [user_id] if user_id else []
            if not users:
                users = Subscription.users_subscribed_to_match(match, NotificationType.MATCH_VIDEO)
            if users:
                cls._send(users, MatchVideoNotification(match))

    @staticmethod
    def ping(client):
        """ Immediately dispatch a Ping to either FCM or a webhook """
        if client.client_type == ClientType.WEBHOOK:
            return TBANSHelper._ping_webhook(client)
        else:
            return TBANSHelper._ping_client(client)

    @staticmethod
    def _ping_client(client):
        client_type = client.client_type
        if client_type in ClientType.FCM_CLIENTS:
            from models.notifications.ping import PingNotification
            notification = PingNotification()

            from models.notifications.requests.fcm_request import FCMRequest
            fcm_request = FCMRequest(firebase_app, notification, tokens=[client.messaging_id])
            logging.info('Ping - {}'.format(str(fcm_request)))

            batch_response = fcm_request.send()
            if batch_response.failure_count > 0:
                response = batch_response.responses[0]
                logging.info('Error Sending Ping - {}'.format(response.exception))
                return False
            else:
                logging.info('Ping Sent')
        elif client_type == ClientType.OS_ANDROID:
            # Send old notifications to Android
            from notifications.ping import PingNotification
            notification = PingNotification()
            notification.send({client_type: [client.messaging_id]})
        else:
            raise Exception('Unsupported FCM client type: {}'.format(client_type))

        return True

    @staticmethod
    def _ping_webhook(client):
        from models.notifications.ping import PingNotification
        notification = PingNotification()

        from models.notifications.requests.webhook_request import WebhookRequest
        webhook_request = WebhookRequest(notification, client.messaging_id, client.secret)
        logging.info('Ping - {}'.format(str(webhook_request)))

        success = webhook_request.send()
        logging.info('Ping Sent')

        return success

    @classmethod
    def schedule_upcoming_match(cls, match, user_id=None):
        from google.appengine.api import taskqueue
        queue = taskqueue.Queue('push-notifications')

        task_name = '{}_match_upcoming'.format(match.key_name)
        # Cancel any previously-scheduled `match_upcoming` notifications for this match
        queue.delete_tasks(taskqueue.Task(name=task_name))

        now = datetime.datetime.utcnow()
        # If we know when our match is starting, schedule to send Xmins before start of match.
        # Otherwise, send immediately.
        if match.time is None or match.time + MATCH_UPCOMING_MINUTES <= now:
            cls.match_upcoming(match, user_id)
        else:
            deferred.defer(
                cls.match_upcoming,
                match,
                user_id,
                _name=task_name,
                _target='backend-tasks',
                _queue='push-notifications',
                _url='/_ah/queue/deferred_notification_send',
                _eta=match.time + MATCH_UPCOMING_MINUTES
            )

    @classmethod
    def schedule_upcoming_matches(cls, event, user_id=None):
        # Schedule `match_upcoming` notifications for Match 1 and Match 2
        # Match 3 (and onward) will be dispatched after Match 1 (or Match N - 2) has been played
        if not event.matches:
            logging.error('Unable to schedule `match_upcoming` notification for {} - no matches'.format(event.key_name))
            return

        from helpers.match_helper import MatchHelper
        next_matches = MatchHelper.upcomingMatches(event.matches, num=2)
        for match in next_matches:
            cls.schedule_upcoming_match(match, user_id)

    @staticmethod
    def verify_webhook(url, secret):
        """ Immediately dispatch a Verification to a webhook """
        from models.notifications.verification import VerificationNotification
        notification = VerificationNotification(url, secret)

        from models.notifications.requests.webhook_request import WebhookRequest
        webhook_request = WebhookRequest(notification, url, secret)
        logging.info('Verification - {}'.format(str(webhook_request)))

        webhook_request.send()
        logging.info('Verification Key - {}'.format(notification.verification_key))

        return notification.verification_key

    @classmethod
    def _send(cls, users, notification):
        # Send to FCM clients
        fcm_clients = MobileClient.clients(users, client_types=ClientType.FCM_CLIENTS)
        if fcm_clients:
            cls._defer_fcm(fcm_clients, notification)

        # Send to webhooks
        webhook_clients = MobileClient.clients(users, client_types=[ClientType.WEBHOOK])
        if webhook_clients:
            cls._defer_webhook(webhook_clients, notification)

    @classmethod
    def _defer_fcm(cls, clients, notification):
        deferred.defer(
            cls._send_fcm,
            clients,
            notification,
            _target='backend-tasks',
            _queue='push-notifications',
            _url='/_ah/queue/deferred_notification_send'
        )

    @classmethod
    def _defer_webhook(cls, clients, notification):
        deferred.defer(
            cls._send_webhook,
            clients,
            notification,
            _target='backend-tasks',
            _queue='push-notifications',
            _url='/_ah/queue/deferred_notification_send'
        )

    @classmethod
    def _send_fcm(cls, clients, notification, backoff_iteration=0):
        # Only send to FCM clients if notifications are enabled
        if not cls._notifications_enabled():
            return 1

        # Only allow so many retries
        backoff_time = 2 ** backoff_iteration
        if backoff_time > MAXIMUM_BACKOFF:
            return 2

        # Make sure we're only sending to FCM clients
        clients = [client for client in clients if client.client_type in ClientType.FCM_CLIENTS]

        from models.notifications.requests.fcm_request import FCMRequest, MAXIMUM_TOKENS
        # We can only send to so many FCM clients at a time - send to our clients across several requests
        for subclients in [clients[i:i + MAXIMUM_TOKENS] for i in range(0, len(clients), MAXIMUM_TOKENS)]:
            fcm_request = FCMRequest(firebase_app, notification, tokens=[client.messaging_id for client in subclients])
            logging.info(str(fcm_request))

            batch_response = fcm_request.send()
            retry_clients = []

            # Handle our failed sends - this might include logging/alerting, removing old clients, or retrying sends
            from firebase_admin.exceptions import InvalidArgumentError, InternalError, UnavailableError
            from firebase_admin.messaging import QuotaExceededError, SenderIdMismatchError, ThirdPartyAuthError, UnregisteredError
            for index, response in enumerate([response for response in batch_response.responses if not response.success]):
                client = subclients[index]
                if isinstance(response.exception, UnregisteredError):
                    logging.info('Deleting unregistered client with ID: {}'.format(client.messaging_id))
                    MobileClient.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, SenderIdMismatchError):
                    logging.info('Deleting mismatched client with ID: {}'.format(client.messaging_id))
                    MobileClient.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, QuotaExceededError):
                    logging.error('Qutoa exceeded - retrying client...')
                    retry_clients.append(client)
                elif isinstance(response.exception, ThirdPartyAuthError):
                    logging.critical('Third party error sending to FCM - {}'.format(response.exception))
                elif isinstance(response.exception, InvalidArgumentError):
                    logging.critical('Invalid argument when sending to FCM - {}'.format(response.exception))
                elif isinstance(response.exception, InternalError):
                    logging.error('Interal FCM error - retrying client...')
                    retry_clients.append(client)
                elif isinstance(response.exception, UnavailableError):
                    logging.error('FCM unavailable - retrying client...')
                    retry_clients.append(client)
                else:
                    debug_string = cls._debug_string(response.exception)
                    logging.error('Unhandled FCM error for {} - {}'.format(client.messaging_id, debug_string))

            if retry_clients:
                # Try again, with exponential backoff
                deferred.defer(
                    cls._send_fcm,
                    retry_clients,
                    notification,
                    backoff_iteration + 1,
                    _countdown=backoff_time,
                    _target='backend-tasks',
                    _queue='push-notifications',
                    _url='/_ah/queue/deferred_notification_send'
                )

        return 0

    @classmethod
    def _send_webhook(cls, clients, notification):
        # Only send to webhooks if notifications are enabled
        if not cls._notifications_enabled():
            return 1

        # Make sure we're only sending to webhook clients
        clients = [client for client in clients if client.client_type == ClientType.WEBHOOK]
        # Only send to verified webhooks
        clients = [client for client in clients if client.verified]

        from models.notifications.requests.webhook_request import WebhookRequest
        for client in clients:
            webhook_request = WebhookRequest(notification, client.messaging_id, client.secret)
            logging.info(str(webhook_request))

            webhook_request.send()

        return 0

    # Returns a list of debug strings for a FirebaseException
    @classmethod
    def _debug_string(cls, exception):
        debug_strings = [exception.code, exception.message]
        if exception.http_response:
            debug_strings.append(str(exception.http_response.json()))
        return ' / '.join(debug_strings)

    @classmethod
    def _notifications_enabled(cls):
        from sitevars.notifications_enable import NotificationsEnable
        return NotificationsEnable.notifications_enabled()
