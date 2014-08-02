import logging

from google.appengine.ext import ndb

from models.mobile_client import MobileClient

class GCMHelper(object):

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
