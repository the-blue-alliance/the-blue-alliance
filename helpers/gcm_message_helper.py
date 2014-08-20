import logging

from consts.push import Push
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMMessage, GCMConnection
from helpers.push_helper import PushHelper
from helpers.model_to_dict import ModelToDict
from models.event import Event


class GCMMessageHelper(object):

    @classmethod
    def send_match_score_update(cls, match):
        users = PushHelper.get_users_subscribed_to_match(match, NotificationType.MATCH_SCORE)
        gcm_keys = PushHelper.get_client_ids_for_users(Push.OS_ANDROID, users)

        if len(gcm_keys) == 0:
            return

        data = {}
        data['message_type'] = NotificationType.MATCH_SCORE
        data['message_data'] = {}
        data['message_data']['event_name'] = match.event.get().name
        data['message_data']['match'] = ModelToDict.matchConverter(match)

        message = GCMMessage(gcm_keys, data)
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)

    @classmethod
    def send_favorite_update(cls, user_id, sending_device_key):

        clients = PushHelper.get_client_ids_for_users("android", [user_id])
        if sending_device_key in clients:
            clients.remove(sending_device_key)
        if len(clients) == 0:
            return

        user_collapse_key = "{}_favorite_update".format(user_id)

        data = {}
        data['message_type'] = NotificationType.UPDATE_FAVORITES
        message = GCMMessage(clients, data, collapse_key=user_collapse_key)
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)

    @classmethod
    def send_subscription_update(cls, user_id, sending_device_key):

        clients = PushHelper.get_client_ids_for_users("android", [user_id])
        if sending_device_key in clients:
            clients.remove(sending_device_key)
        if len(clients) == 0:
            return

        user_collapse_key = "{}_subscription_update".format(user_id)

        data = {}
        data['message_type'] = NotificationType.UPDATE_SUBSCRIPTIONS
        message = GCMMessage(clients, data, collapse_key=user_collapse_key)
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)
