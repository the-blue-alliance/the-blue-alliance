import datetime
import json

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from controllers.api.api_status_controller import ApiStatusController

from helpers.push_helper import PushHelper

from models.event import Event
from models.sitevar import Sitevar

from notifications.alliance_selections import AllianceSelectionNotification
from notifications.level_starting import CompLevelStartingNotification
from notifications.broadcast import BroadcastNotification
from notifications.match_score import MatchScoreNotification
from notifications.match_video import MatchVideoNotification, EventMatchVideoNotification
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
    def send_upcoming_match_notification(cls, match, event):
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
        match.dirty = True
        from helpers.match_manipulator import MatchManipulator
        MatchManipulator.createOrUpdate(match)

    @classmethod
    def send_upcoming_matches(cls, live_events):
        from helpers.match_helper import MatchHelper  # PJL: Hacky :P
        # Causes circular import, otherwise
        # https://github.com/the-blue-alliance/the-blue-alliance/pull/1098#discussion_r25128966

        down_events = []
        now = datetime.datetime.utcnow()
        for event in live_events:
            matches = event.matches
            if not matches:
                continue
            last_matches = MatchHelper.recentMatches(matches, num=1)
            next_matches = MatchHelper.upcomingMatches(matches, num=2)

            # First, compare the difference between scheduled times of next/last match
            # Send an upcoming notification if it's <10 minutes, to account for events ahead of schedule
            if last_matches != []:
                last_match = last_matches[0]
                for i, next_match in enumerate(next_matches):
                    if not next_match.push_sent and last_match.time and next_match.time:
                        diff = next_match.time - last_match.time
                        if diff < datetime.timedelta(minutes=10 * (i + 1)):
                            cls.send_upcoming_match_notification(next_match, event)

            for match in next_matches:
                if match and not match.push_sent:
                    # Only continue sending for the next match if a push hasn't already been sent for it
                    if match.time is None or match.time + datetime.timedelta(minutes=-7) <= now:
                        # Only send notifications for matches no more than 7 minutes (average-ish match cycle time) before it's scheduled to start
                        # Unless, the match has no time info. Then #yolo and send it
                        cls.send_upcoming_match_notification(match, event)

            # Determine if event is down
            if cls.is_event_down(last_matches[0] if last_matches else None, next_matches[0] if next_matches else None):
                down_events.append(event.key_name)

        # Update the status sitevar
        status_sitevar = Sitevar.get_by_id('apistatus.down_events')
        if status_sitevar is None:
            status_sitevar = Sitevar(id="apistatus.down_events", description="A list of down event keys", values_json="[]")
        old_status = status_sitevar.contents

        status_sitevar.contents = down_events
        status_sitevar.put()

        # Clear API Response cache
        ApiStatusController.clear_cache_if_needed(old_status, down_events)

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
    def send_match_video(cls, match):
        """
        Sends match_video and event_match_video notifications
        If the match is current, MatchVideoNotification is sent.
        Otherwise, EventMatchVideoNotification is sent
        """
        match_users = set(PushHelper.get_users_subscribed_to_match(match, NotificationType.MATCH_VIDEO))
        event_users = set(PushHelper.get_users_subscribed_to_event(match.event.get(), NotificationType.MATCH_VIDEO))
        users = match_users.union(event_users)
        if match.within_seconds(60*10):
            user_keys = PushHelper.get_client_ids_for_users(users)
            MatchVideoNotification(match).send(user_keys)
        else:
            user_keys = PushHelper.get_client_ids_for_users(users)
            EventMatchVideoNotification(match).send(user_keys)

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

    @classmethod
    def is_event_down(cls, last_match, next_match):
        """
        Determines if an event's reporting is "down".
        Conditions should be pretty tight, don't want false positives
        Both next and last match need to be on the same day.
        Use scheduled/actual start times for last to determine schedule offset
        After max(predicted, scheduled) for next + threshold, event is down
        """
        if not last_match or not next_match:
            return False

        if not last_match.time or not last_match.actual_time or not next_match.time:
            # Don't cause false positives when we're missing data
            return False

        if not last_match.time.day == next_match.time.day:
            # Events are on different days, all bets are off
            return False

        now = datetime.datetime.utcnow()
        threshold = datetime.timedelta(minutes=30)  # we can tune this
        schedule_offset = last_match.actual_time - last_match.time
        predicted_start = max(next_match.time + schedule_offset, next_match.time)

        if now > predicted_start + threshold:
            # Event is down :(
            return True
        return False
