import json
import logging
import tba_config
import time

from google.appengine.ext import deferred
from google.appengine.api import urlfetch

from models.sitevar import Sitevar


class FirebasePusher(object):
    SUCCESS_STATUS_CODES = {200, 204}

    @classmethod
    def _put_data(cls, key, data_json):
        firebase_secrets = Sitevar.get_by_id("firebase.secrets")
        if firebase_secrets is None:
            raise Exception("Missing sitevar: firebase.secrets. Can't write to Firebase.")
        FIREBASE_SECRET = firebase_secrets.contents['FIREBASE_SECRET']

        url = tba_config.CONFIG['firebase-url'].format(key, FIREBASE_SECRET)
        result = urlfetch.fetch(url, data_json, 'PUT')
        if result.status_code not in cls.SUCCESS_STATUS_CODES:
            logging.warning("Error pushing data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

    @classmethod
    def match_to_payload_dict(cls, match):
        return {'key_name': match.key_name,
                'comp_level': match.comp_level,
                'match_number': match.match_number,
                'set_number': match.set_number,
                'alliances': match.alliances,
                'winning_alliance': match.winning_alliance}

    @classmethod
    def update_match(cls, match):
        payload_key = 'events/{}/matches/{}'.format(match.event.id(), match.key_name)
        payload_data_json = json.dumps(cls.match_to_payload_dict(match))

        deferred.defer(cls._put_data, payload_key, payload_data_json, _queue="firebase")
