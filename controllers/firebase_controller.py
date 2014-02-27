import logging

from google.appengine.ext import webapp
from google.appengine.api import urlfetch

from models.sitevar import Sitevar

import tba_config
import json


class FirebasePushDo(webapp.RequestHandler):
    """
    Pushes data to Firebase
    """
    SUCCESS_STATUS_CODES = {200, 204}

    def post(self):
        payload = json.loads(self.request.body)
        key = payload['key']
        payload_json = json.dumps(payload['data'])

        firebase_secrets = Sitevar.get_by_id("firebase.secrets")
        if firebase_secrets is None:
            raise Exception("Missing sitevar: firebase.secrets. Can't write to Firebase.")
        FIREBASE_SECRET = firebase_secrets.contents['FIREBASE_SECRET']

        url = tba_config.CONFIG['firebase-url'].format(key, FIREBASE_SECRET)
        result = urlfetch.fetch(url, payload_json, 'PUT')
        if result.status_code not in self.SUCCESS_STATUS_CODES:
            logging.warning("Error pushing data to Firebase: {}. ERROR {}: {}".format(payload_json, result.status_code, result.content))
