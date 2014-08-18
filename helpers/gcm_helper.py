import logging

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import users

#from helpers.gcm_message_helper import GCMMessageHelper

from models.mobile_client import MobileClient
from models.subscription import Subscription
from models.user import User


class MobileUser(db.Model):
    '''
    Used in workaround for null user id (see below)
    We can restructure this once regular oauth logins happen (https://github.com/the-blue-alliance/the-blue-alliance/issues/1069)
    This is not a good long term solution, I don't think
    '''
    user = db.UserProperty(required=True)


class GCMHelper(object):

    @classmethod
    def user_email_to_id(cls, user_email):
        '''
        Returns the user id for a given email address (or None if invalid)
        workaround for this bug: https://code.google.com/p/googleappengine/issues/detail?id=8848
        solution from: http://stackoverflow.com/questions/816372/how-can-i-determine-a-user-id-based-on-an-email-address-in-app-engine
        '''
        u = users.User(user_email)
        key = MobileUser(user=u).put()
        obj = MobileUser.get(key)
        return obj.user.user_id()

    @classmethod
    def delete_bad_gcm_token(cls, key):
        logging.info("removing bad GCM token: "+key)
        to_delete = MobileClient.query(MobileClient.messaging_id == key).fetch()
        ndb.delete_multi([m.key for m in to_delete])

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
        keys = match.team_key_names
        keys.append(match.key_name)
        keys.append(match.event.id())
        logging.info("Getting subscriptions for keys: "+str(keys))
        users = Subscription.query(Subscription.model_key.IN(keys), projection=[Subscription.user_id, Subscription.settings_json], distinct=True).fetch()
        output = []
        for user in users:
            logging.info("User settings: "+str(user.settings))
            if notification in user.settings:
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
