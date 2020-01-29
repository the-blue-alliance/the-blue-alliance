import logging

from collections import defaultdict

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.api import memcache

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from models.account import Account
from models.mobile_client import MobileClient
from models.mobile_user import MobileUser
from models.subscription import Subscription
from models.user import User


class PushHelper(object):

    """
    General helper methods for push notifications
    Actual notifications should be built and send from NotificationHelper
    (they're split up for cleanliness)
    """

    @classmethod
    def notification_enums_from_string(cls, notifications):
        out = []
        for notification in notifications:
            out.append(NotificationType.types[notification])
        return out

    @classmethod
    def notification_string_from_enums(cls, notifications):
        out = []
        for notification in notifications:
            out.append(NotificationType.type_names[notification])
        return out

    @classmethod
    def user_email_to_id(cls, user_email):
        """
        Returns the user id for a given email address (or None if invalid)
        workaround for this bug: https://code.google.com/p/googleappengine/issues/detail?id=8848
        solution from: http://stackoverflow.com/questions/816372/how-can-i-determine-a-user-id-based-on-an-email-address-in-app-engine
        """
        cache_key = 'PushHelper.user_email_to_id():{}'.format(user_email)
        user_id = memcache.get(cache_key)
        if user_id is None:
            u = users.User(user_email)
            key = MobileUser(user=u).put()
            obj = key.get()
            user_id = obj.user.user_id()
            key.delete()
            memcache.set(cache_key, user_id, 60*10)

        if Account.get_by_id(user_id) is None:
            # Create an account for this user
            nickname = user_email.split('@')[0]
            Account(id=user_id, email=user_email, nickname=nickname, display_name=nickname, registered=False).put()

        return user_id

    @classmethod
    def delete_bad_gcm_token(cls, key):
        logging.info("removing bad GCM token: {}".format(key))
        to_delete = MobileClient.query(MobileClient.messaging_id == key).fetch(keys_only=True)
        ndb.delete_multi(to_delete)

    @classmethod
    def update_token(cls, old, new):
        to_update = MobileClient.query(MobileClient.messaging_id == old).fetch()
        for model in to_update:
            model.messaging_id = new
            model.put()

    @classmethod
    def get_users_subscribed(cls, model_key):
        user_list = Subscription.query(Subscription.model_key == model_key).fetch()
        output = []
        for user in user_list:
            output.append(user.user_id)
        return output

    @classmethod
    def get_users_subscribed_to_match(cls, match, notification):
        keys = []
        for team in match.team_key_names:
            keys.append(team)
            keys.append("{}_{}".format(match.event_key_name, team))

        keys.append("{}*".format(match.year))  # key for all events in year
        keys.append(match.key_name)
        keys.append(match.event_key_name)
        users = Subscription.query(Subscription.model_key.IN(keys), Subscription.notification_types == notification).fetch()
        output = []
        for user in users:
            output.append(user.user_id)
        return output

    @classmethod
    def get_users_subscribed_for_alliances(cls, event, notification):
        keys = []
        for team in event.alliance_teams:
            keys.append(team)
            keys.append("{}_{}".format(event.key_name, team))  # team@event key
        keys.append("{}*".format(event.year))  # key for all events in year
        keys.append(event.key_name)
        users = Subscription.query(Subscription.model_key.IN(keys), Subscription.notification_types == notification).fetch()
        output = [user.user_id for user in users]
        return output

    @classmethod
    def get_client_ids_for_users(cls, user_list, os_types=None):
        if not user_list:
            return defaultdict(list)

        if os_types is None:
            os_types = ClientType.names.keys()
        clients = MobileClient.query(MobileClient.user_id.IN(user_list), MobileClient.client_type.IN(os_types), MobileClient.verified == True).fetch()
        return cls.get_client_ids_for_clients(clients)

    @classmethod
    def get_client_ids_for_clients(cls, clients):
        output = defaultdict(list)
        for client in clients:
            if client.client_type == ClientType.WEBHOOK:
                output[client.client_type].append((client.messaging_id, client.secret))
            else:
                output[client.client_type].append(client.messaging_id)
        return output
