import datetime
import logging
import urllib
import uuid

from consts.client_type import ClientType
from consts.notification_type import NotificationType

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
            next_matchs = MatchHelper.upcomingMatches(matches, num=2)
            for match in next_matches:
                if match and not match.push_sent:
                    # Only continue sending for the next match if a push hasn't already been sent for it
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

                        # Send upcoming match notification
                        notification = UpcomingMatchNotification(match, event)
                        notification.send(keys)
                        match.push_sent = True  # Make sure we don't send updates for this match again
                        match.put()

                        # Don't send update for any further matches
                        return

    @classmethod
    def send_schedule_update(cls, event):
        users = PushHelper.get_users_subscribed_to_event(event, NotificationType.SCHEDULE_UPDATED)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = ScheduleUpdatedNotification(event)
        notification.send(keys)

    @classmethod
    def send_alliance_update(cls, event):
        users = PushHelper.get_users_subscribed_for_alliances(event, NotificationType.ALLIANCE_SELECTION)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = AllianceSelectionNotification(event)
        notification.send(keys)

    @classmethod
    def send_award_update(cls, event):
        users = PushHelper.get_users_subscribed_to_event(event, NotificationType.AWARDS)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = AwardsUpdatedNotification(event)
        notification.send(keys)

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
