import logging

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from helpers.push_helper import PushHelper
from models.event import Event
from notifications.match_score import MatchScoreNotification
from notifications.update_favorites import UpdateFavoritesNotification
from notifications.update_subscriptions import UpdateSubscriptionsNotification


class NotificationHelper(object):

    '''
    Helper class for sending push notifications.
    Methods here should build a Notification object and use their send method
    '''

    @classmethod
    def send_match_score_update(cls, match):
        users = PushHelper.get_users_subscribed_to_match(match, NotificationType.MATCH_SCORE)
        keys = PushHelper.get_client_ids_for_users(users)

        notification = MatchScoreNotification(match)
        notification.send(keys)

    @classmethod
    def send_favorite_update(cls, user_id, sending_device_key):
        clients = PushHelper.get_client_ids_for_users([user_id])

        notification = UpdateFavoritesNotification(user_id, sending_device_key)
        notification.send(clients)

    @classmethod
    def send_subscription_update(cls, user_id, sending_device_key):
        clients = PushHelper.get_client_ids_for_users("android", [user_id])

        notification = UpdateSubscriptionsNotification(user_id, sending_device_key)
        notification.send(clients)
