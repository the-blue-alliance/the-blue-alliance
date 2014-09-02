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
        gcm_keys = PushHelper.get_client_ids_for_users(ClientType.names[ClientType.OS_ANDROID], users)

        if len(gcm_keys) == 0:
            return

        notification = MatchScoreNotification(match)
        notification.send({ClientType.OS_ANDROID: gcm_keys})

    @classmethod
    def send_favorite_update(cls, user_id, sending_device_key):

        clients = PushHelper.get_client_ids_for_users("android", [user_id])
        if sending_device_key in clients:
            clients.remove(sending_device_key)
        if len(clients) == 0:
            return

        notification = UpdateFavoritesNotification(user_id)
        notification.send({ClientType.OS_ANDROID: clients})

    @classmethod
    def send_subscription_update(cls, user_id, sending_device_key):

        clients = PushHelper.get_client_ids_for_users("android", [user_id])
        if sending_device_key in clients:
            clients.remove(sending_device_key)
        if len(clients) == 0:
            return

        notification = UpdateSubscriptionsNotification(user_id)
        notification.send(ClientType.OS_ANDROID, {ClientType.OS_ANDROID: clients})
