import datetime
import json
import logging
import tba_config

from google.appengine.ext import deferred
from google.appengine.api import urlfetch

from database.dict_converters.match_converter import MatchConverter
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
        """
        Remove data from the specified Firebase database reference.
        """
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, method='DELETE', deadline=10)
        if result.status_code != 204:
            logging.warning("Error wirht DELETE data from Firebase: {}. ERROR {}: {}".format(url, result.status_code, result.content))

    @classmethod
    def _put_data(cls, key, data_json):
        """
        Write or replace data to a defined path, like messages/users/user1/<data>
        """
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='PUT', deadline=10)
        if result.status_code != 200:
            logging.warning("Error with PUT data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

    @classmethod
    def _push_data(cls, key, data_json):
        """
        Add to a list of data in our Firebase database.
        Every time we send a POST request, the Firebase client generates a unique key, like messages/users/<unique-id>/<data>
        """
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='POST', deadline=10)
        if result.status_code != 200:
            logging.warning("Error with POST data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

    @classmethod
    def delete_match(cls, match):
        """
        Deletes a match from an event and event_team
        """
        deferred.defer(
            cls._delete_data,
            'events/{}/matches/{}'.format(match.event.id(), match.key.id()),
            _queue="firebase")

        for team_key_name in match.team_key_names:
            deferred.defer(
            cls._delete_data,
            'event_teams/{}_{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
            _queue="firebase")

    @classmethod
    def update_match(cls, match):
        """
        Updates a match in an event and event/team
        """
        match_data_json = json.dumps(MatchConverter.convert(match, 3))

        deferred.defer(
            cls._put_data,
            'events/{}/matches/{}'.format(match.event.id(), match.key.id()),
            match_data_json,
            _queue="firebase")

        for team_key_name in match.team_key_names:
            deferred.defer(
                cls._put_data,
                'event_teams/{}_{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
                match_data_json,
                _queue="firebase")
