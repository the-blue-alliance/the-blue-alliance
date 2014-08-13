import logging

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import users

from models.mobile_client import MobileClient
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
