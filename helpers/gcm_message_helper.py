import logging

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMConnection
from helpers.push_helper import PushHelper
from models.event import Event
from notifications.match_score import MatchScoreNotification
from notifications.update_favorites import UpdateFavoritesNotification
from notifications.update_subscriptions import UpdateSubscriptionsNotification


class GCMMessageHelper(object):

    @classmethod
    def send_match_score_update(cls, match):
        users = PushHelper.get_users_subscribed_to_match(match, NotificationType.MATCH_SCORE)
        gcm_keys = PushHelper.get_client_ids_for_users(ClientType.names[ClientType.OS_ANDROID], users)

        if len(gcm_keys) == 0:
            return

        notification = MatchScoreNotification(match)
        message = notification.build(ClientType.OS_ANDROID, {ClientType.OS_ANDROID: gcm_keys})
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)

    @classmethod
    def send_favorite_update(cls, user_id, sending_device_key):

        clients = PushHelper.get_client_ids_for_users("android", [user_id])
        if sending_device_key in clients:
            clients.remove(sending_device_key)
        if len(clients) == 0:
            return

        notification = UpdateFavoritesNotification(user_id)
        message = notification.build(ClientType.OS_ANDROID, {ClientType.OS_ANDROID: clients})
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)

    @classmethod
    def send_subscription_update(cls, user_id, sending_device_key):

        clients = PushHelper.get_client_ids_for_users("android", [user_id])
        if sending_device_key in clients:
            clients.remove(sending_device_key)
        if len(clients) == 0:
            return

        notification = UpdateSubscriptionsNotification(user_id)
        message = notification.build(ClientType.OS_ANDROID, {ClientType.OS_ANDROID: clients})
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)
