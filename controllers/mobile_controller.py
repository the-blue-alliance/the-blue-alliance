import json
import logging
import webapp2

from models.mobile_client import MobileClient

class MobileRegistrationController(webapp2.RequestHandler):
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
        super(NotificationRegistrationController, self).__init__( *args, **kw)
        self.checksum = self.request.headers[self.REQUEST_CHECKSUM]
        self.request_data = self.request.body

    def validate_checksum(self, checksum, data):
        # TODO Get secret salt from ENV variable, hash the data and compare
        return True

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
