import datetime
import logging
import urllib
import uuid

from consts.client_type import ClientType
from consts.notification_type import NotificationType

from google.appengine.ext import deferred
from google.appengine.api import urlfetch

from helpers.push_helper import PushHelper

from models.event import Event
from models.sitevar import Sitevar

from notifications.alliance_selections import AllianceSelectionNotification
from notifications.level_starting import CompLevelStartingNotification
from notifications.broadcast import BroadcastNotification
from notifications.match_score import MatchScoreNotification
from notifications.awards_updated import AwardsUpdatedNotification
from notifications.schedule_updated import ScheduleUpdatedNotification
from notifications.upcoming_match import UpcomingMatchNotification
from notifications.update_favorites import UpdateFavoritesNotification
from notifications.update_subscriptions import UpdateSubscriptionsNotification
from notifications.verification import VerificationNotification


# used for deferred call
def track_notification(notification_type_enum, num_keys):
    """
    For more information about GAnalytics Protocol Parameters, visit
    https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
    """
    analytics_id = Sitevar.get_by_id("google_analytics.id")
    if analytics_id is None:
        logging.warning("Missing sitevar: google_analytics.id. Can't track API usage.")
    else:
        GOOGLE_ANALYTICS_ID = analytics_id.contents['GOOGLE_ANALYTICS_ID']
        params = urllib.urlencode({
            'v': 1,
            'tid': GOOGLE_ANALYTICS_ID,
            'cid': uuid.uuid3(uuid.NAMESPACE_X500, str('tba-notification-tracking')),
            't': 'event',
            'ec': 'notification',
            'ea': NotificationType.type_names[notification_type_enum],
            'ev': num_keys,
            'ni': 1,
            'sc': 'end',  # forces tracking session to end
        })

        analytics_url = 'http://www.google-analytics.com/collect?%s' % params
        urlfetch.fetch(
            url=analytics_url,
            method=urlfetch.GET,
            deadline=10,
        )


class NotificationHelper(object):

    """
    Helper class for sending push notifications.
    Methods here should build a Notification object and use their send method
    """

    @classmethod
    def send_match_score_update(cls, match):
        users = PushHelper.get_users_subscribed_to_match(match, NotificationType.MATCH_SCORE)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = MatchScoreNotification(match)
        notification.send(keys)

        deferred.defer(track_notification, NotificationType.MATCH_SCORE, len(keys), _queue="api-track-call")

    @classmethod
    def send_favorite_update(cls, user_id, sending_device_key=""):
        clients = PushHelper.get_client_ids_for_users([user_id])

        notification = UpdateFavoritesNotification(user_id, sending_device_key)
        notification.send(clients)

    @classmethod
    def send_subscription_update(cls, user_id, sending_device_key=""):
        clients = PushHelper.get_client_ids_for_users([user_id])

        notification = UpdateSubscriptionsNotification(user_id, sending_device_key)
        notification.send(clients)

    @classmethod
    def send_upcoming_matches(cls, live_events):
        from helpers.match_helper import MatchHelper  # PJL: Hacky :P
        # Causes circular import, otherwise
        # https://github.com/the-blue-alliance/the-blue-alliance/pull/1098#discussion_r25128966

        now = datetime.datetime.utcnow()
        for event in live_events:
            matches = event.matches
            if not matches:
                continue
            next_match = MatchHelper.upcomingMatches(matches, num=1)
            if next_match[0] and not next_match[0].push_sent:
                # Only continue sending for the next match if a push hasn't already been sent for it
                match = next_match[0]
                if match.time is None or match.time + datetime.timedelta(minutes=-7) <= now:
                    # Only send notifications for matches no more than 7 minutes (average-ish match cycle time) before it's scheduled to start
                    # Unless, the match has no time info. Then #yolo and send it
                    users = PushHelper.get_users_subscribed_to_match(match, NotificationType.UPCOMING_MATCH)
                    keys = PushHelper.get_client_ids_for_users(users)

                    if match.set_number == 1 and match.match_number == 1:
                        # First match of a new type, send level starting notifications
                        start_users = PushHelper.get_users_subscribed_to_match(match, NotificationType.LEVEL_STARTING)
                        start_keys = PushHelper.get_client_ids_for_users(start_users)
                        level_start = CompLevelStartingNotification(match, event)
                        level_start.send(start_keys)

                        deferred.defer(track_notification, NotificationType.LEVEL_STARTING, len(start_keys), _queue="api-track-call")

                    # Send upcoming match notification
                    notification = UpcomingMatchNotification(match, event)
                    notification.send(keys)
                    match.push_sent = True  # Make sure we don't send updates for this match again
                    match.put()

                    deferred.defer(track_notification, NotificationType.UPCOMING_MATCH, len(keys), _queue="api-track-call")

    @classmethod
    def send_schedule_update(cls, event):
        users = PushHelper.get_users_subscribed_to_event(event, NotificationType.SCHEDULE_UPDATED)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = ScheduleUpdatedNotification(event)
        notification.send(keys)

        deferred.defer(track_notification, NotificationType.SCHEDULE_UPDATED, len(keys), _queue="api-track-call")

    @classmethod
    def send_alliance_update(cls, event):
        users = PushHelper.get_users_subscribed_for_alliances(event, NotificationType.ALLIANCE_SELECTION)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = AllianceSelectionNotification(event)
        notification.send(keys)

        deferred.defer(track_notification, NotificationType.ALLIANCE_SELECTION, len(keys), _queue="api-track-call")

    @classmethod
    def send_award_update(cls, event):
        users = PushHelper.get_users_subscribed_to_event(event, NotificationType.AWARDS)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = AwardsUpdatedNotification(event)
        notification.send(keys)

        deferred.defer(track_notification, NotificationType.AWARDS, len(keys), _queue="api-track-call")

    @classmethod
    def send_broadcast(cls, client_types, title, message, url, app_version=''):
        users = PushHelper.get_all_mobile_clients(client_types)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = BroadcastNotification(title, message, url, app_version)
        notification.send(keys)

    @classmethod
    def verify_webhook(cls, url, secret):
        key = {ClientType.WEBHOOK: [(url, secret)]}
        notification = VerificationNotification(url, secret)
        notification.send(key)
        return notification.verification_key
