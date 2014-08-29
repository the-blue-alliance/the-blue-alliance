import logging

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import users

from consts.notification_type import NotificationType
from models.account import Account
from models.mobile_client import MobileClient
from models.mobile_user import MobileUser
from models.subscription import Subscription
from models.user import User


class PushHelper(object):

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
        '''
        Returns the user id for a given email address (or None if invalid)
        workaround for this bug: https://code.google.com/p/googleappengine/issues/detail?id=8848
        solution from: http://stackoverflow.com/questions/816372/how-can-i-determine-a-user-id-based-on-an-email-address-in-app-engine
        '''
        u = users.User(user_email)
        key = MobileUser(user=u).put()
        obj = key.get()
        user_id = obj.user.user_id()
        key.delete()

        if Account.get_by_id(user_id) is None:
            # Create an account for this user
            Account(id=user_id, email = user_email, nickname = user_email.split('@')[0], registered = False).put()

        return user_id

    @classmethod
    def delete_bad_gcm_token(cls, key):
        logging.info("removing bad GCM token: "+key)
        to_delete = MobileClient.query(MobileClient.messaging_id == key).fetch(keys_only=True)
        ndb.delete_multi(to_delete)

    @classmethod
    def update_token(cls, old, new):
        logging.info("updating token"+old+"\n->"+new)
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
            keys.append("{}_{}".format(match.event.id(), team))
        keys.append(match.key_name)
        keys.append(match.event.id())
        logging.info("Getting subscriptions for keys: "+str(keys))
        users = Subscription.query(Subscription.model_key.IN(keys), Subscription.notification_types == notification).fetch()
        output = []
        for user in users:
            output.append(user.user_id)
        return output

    @classmethod
    def get_client_ids_for_users(cls, os_type, user_list):
        output = []
        for user in user_list:
            client_list = MobileClient.query(MobileClient.user_id == user, MobileClient.operating_system == os_type).fetch()
            for client in client_list:
                output.append(client.messaging_id)
        return output
