import logging

from google.appengine.ext import ndb

from models.mobile_client import MobileClient

class GCMHelper():

    def delete_bad_gcm_token(key):
        logging.info("removing bad GCM token: "+key)
        to_delete_future = MobileClient.query(MobileClient.messaging_id == key).fetch_async()
        ndb.delete_multi([m.get_result().key for m in to_delete_future ])

    def update_token(old, new):
        logging.info("updating token"+old+"\n->"+new)    
        to_update_future = MobileClient.query(MobileClient.messaging_id == old).fetch_async()
        for model in to_update_future:
            model.get_result()
            model.messaging_id = new
            model.put()
