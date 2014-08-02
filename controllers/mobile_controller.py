import hashlib
import json
import logging
import webapp2

from controllers.gcm.gcm import GCMMessage, GCMConnection
from helpers.gcm_helper import GCMHelper
from models.mobile_client import MobileClient
from models.sitevar import Sitevar

class BaseIncomingMessageController(webapp2.RequestHandler):
    
    REQUEST_CHECKSUM = "checksum"   

    def __init__(self, *args, **kw):
        super(BaseIncomingMessageController, self).__init__(*args, **kw)
        self.checksum = self.request.headers[self.REQUEST_CHECKSUM]    
        self.request_data = self.request.body

    def validate_checksum(self, checksum, data):
        secret_sitevar = Sitevar.get_by_id('gcm.checksumSecret')
        if secret_sitevar is None:
            raise Exception("Sitevar mobile.secretKey in undefined. Can't process incoming requests")
        secret_key = str(secret_sitevar.values_json)
        expected_hash = hashlib.sha256(str(secret_key+data).encode()).hexdigest()
        logging.info("secret: "+str(secret_key)+"!")
        logging.info("data: "+str(data))
        logging.info("Expected hash: "+expected_hash)
        logging.info("Got hash: "+checksum) 
        return expected_hash == checksum

    def post(self, *args, **kw):
        pass


class MobileRegistrationController(BaseIncomingMessageController):
    '''
    When GCM (and in the future, other systems) clients register,
    they will send a POST request here. That request will contain the 
    user's GCM key (or whatever other key) and a messaging key unique 
    to that user. For more info on the Cloud <-> Device messaging protocol,
    see this link (for android): 
    https://github.com/google/iosched/blob/master/doc/GCM.md#gcm-key

    The request will also come with a checksum header, which contains request body
    salted with a secret key.
    '''

    REQUEST_CHECKSUM = "checksum"
    GCM_REGISTRATION_ID = "gcm_registration_id"
    GCM_KEY = "gcm_key"

    def __init__(self, *args, **kw):
        super(MobileRegistrationController, self).__init__( *args, **kw)


    def post(self, *args, **kw):
        if not self.validate_checksum(self.checksum, self.request_data):
            self.response.set_status(401)
            return
        data = json.loads(self.request_data)

        gcmId = data[self.GCM_REGISTRATION_ID]
        userKey = data[self.GCM_KEY]

        if len(MobileClient.query( MobileClient.messaging_id==gcmId, MobileClient.user_key==userKey ).fetch()) == 0:
            # Record doesn't exist yet, so add it
            MobileClient(   messaging_id = gcmId,
                            user_key = userKey ).put()        
            logging.info("GCM KEY: "+gcmId)
            logging.info("USER ID: "+userKey)

class AddFavoriteController(BaseIncomingMessageController):

    USER_KEY = "user_key"
    MODEL_KEY = "model_key"

    def __init__(self, *args, **kw):
        super(AddFavoriteController, self).__init__(*args, **kw)

    def post(self, *args, **kw):
        if not self.validate_checksum(self.checksum, self.request_data):
            self.response.set_status(401)
            return
        data = json.loads(self.request_data)

        userKey = data[self.USER_KEY]
        modelKey = data[self.MODEL_KEY] 

        if Favorite.query( Favorite.user_key == userKey, Favorite.model_key == modelKey).count() == 0:
            # Favorite doesn't exist, add it
            Favorite( user_key = userKey, model_key = modle_key).put()

            logging.info("Added favorite: "+userKey+"/"+modelKey)


class MobileTestMessageController(webapp2.RequestHandler):

    def get(self, *args, **kw):
        gcmId = self.request.get("id")
        message_dict = {}
        message_dict["message_type"] = "gcm"
        message_dict["message_data"] = {"type": "test", "title": "Test Notification", "desc": "Foobar"}
        message = GCMMessage(gcmId, message_dict) 
        logging.info("Sending message to: "+gcmId)
        connection = GCMConnection() 
        connection.notify_device(message)

class MobileTokenDeleteController(webapp2.RequestHandler):
    
    def get(self, *args, **kw):
        token = self.request.get("id")
        GCMHelper.delete_bad_gcm_token(token)

class MobileTokenUpdateController(webapp2.RequestHandler):
    
    def get(self, *args, **kw):
        old = self.request.get("old")
        new = self.request.get("new")
        GCMHelper.update_token(old, new)
