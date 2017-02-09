import datetime
import json
import logging
import tba_config

from google.appengine.ext import deferred
from google.appengine.api import urlfetch

from models.sitevar import Sitevar


class FirebasePusher(object):
    @classmethod
    def _get_secret(cls):
        firebase_secrets = Sitevar.get_by_id("firebase.secrets")
        if firebase_secrets is None:
            logging.error("Missing sitevar: firebase.secrets. Can't write to Firebase.")
            return None
        return firebase_secrets.contents['FIREBASE_SECRET']

    @classmethod
    def _delete_data(cls, key):
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, method='DELETE', deadline=10)
        if result.status_code != 204:
            logging.warning("Error deleting data from Firebase: {}. ERROR {}: {}".format(url, result.status_code, result.content))

    @classmethod
    def _put_data(cls, key, data_json):
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='PUT', deadline=10)
        if result.status_code != 200:
            logging.warning("Error pushing data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

    @classmethod
    def _push_data(cls, key, data_json):
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='POST', deadline=10)
        if result.status_code != 200:
            logging.warning("Error pushing data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

    @classmethod
    def match_to_payload_dict(cls, match):
        return {'key_name': match.key_name,
                'comp_level': match.comp_level,
                'match_number': match.match_number,
                'set_number': match.set_number,
                'alliances': match.alliances,
                'winning_alliance': match.winning_alliance,
                'order': match.play_order}

    @classmethod
    def delete_match(cls, match):
        payload_key = 'events/{}/matches/{}'.format(match.event.id(), match.key_name)

        deferred.defer(cls._delete_data, payload_key, _queue="firebase")

    @classmethod
    def update_match(cls, match):
        payload_key = 'events/{}/matches/{}'.format(match.event.id(), match.key_name)
        payload_data_json = json.dumps(cls.match_to_payload_dict(match))

        deferred.defer(cls._put_data, payload_key, payload_data_json, _queue="firebase")
