import datetime
import json
import logging
import tba_config

from google.appengine.ext import deferred
from google.appengine.api import urlfetch

from controllers.apiv3.model_properties import filter_match_properties
from database.dict_converters.match_converter import MatchConverter
from database.dict_converters.event_converter import EventConverter
from database.dict_converters.event_details_converter import EventDetailsConverter
from helpers.event_helper import EventHelper
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
        if not tba_config.CONFIG['firebase-push']:
            return
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, method='DELETE', deadline=10)
        if result.status_code not in {200, 204}:
            raise Exception("Error with DELETE data from Firebase: {}. ERROR {}: {}".format(url, result.status_code, result.content))

    @classmethod
    def _put_data(cls, key, data_json):
        """
        Write or replace data to a defined path, like messages/users/user1/<data>
        """
        if not tba_config.CONFIG['firebase-push']:
            return
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='PUT', deadline=10)
        if result.status_code != 200:
            raise Exception("Error with PUT data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

    @classmethod
    def _push_data(cls, key, data_json):
        """
        Add to a list of data in our Firebase database.
        Every time we send a POST request, the Firebase client generates a unique key, like messages/users/<unique-id>/<data>
        """
        if not tba_config.CONFIG['firebase-push']:
            return
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='POST', deadline=10)
        if result.status_code != 200:
            raise Exception("Error with POST data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

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
            'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
            _queue="firebase")

    @classmethod
    def replace_event_matches(cls, event_key, matches):
        """
        Deletes matches from an event and puts these instead
        """

        match_data = {}
        for match in matches:
            match_data[match.key.id()] = filter_match_properties([MatchConverter.convert(match, 3)], 'simple')[0]
        deferred.defer(
            cls._put_data,
            'events/{}/matches'.format(event_key),
            json.dumps(match_data),
            _queue="firebase")

    @classmethod
    def update_match(cls, match):
        """
        Updates a match in an event and event/team
        """
        if match.year < 2017:
            return

        match_data_json = json.dumps(filter_match_properties([MatchConverter.convert(match, 3)], 'simple')[0])

        deferred.defer(
            cls._put_data,
            'events/{}/matches/{}'.format(match.event.id(), match.key.id()),
            match_data_json,
            _queue="firebase")

        for team_key_name in match.team_key_names:
            deferred.defer(
                cls._put_data,
                'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
                match_data_json,
                _queue="firebase")

    @classmethod
    def update_event_details(cls, event_details):
        """
        Updates an event_detail in an event
        """
        if int(event_details.key.id()[:4]) < 2017:
            return

        event_details_json = json.dumps(EventDetailsConverter.convert(event_details, 3))

        deferred.defer(
            cls._put_data,
            'events/{}/details'.format(event_details.key.id()),
            event_details_json,
            _queue="firebase")

    @classmethod
    def update_event_team_status(cls, event_key, team_key, status):
        """
        Updates an event team status
        """
        if int(event_key[:4]) < 2017:
            return

        from helpers.event_team_status_helper import EventTeamStatusHelper  # Prevent circular import

        if status:
            status.update({
                'alliance_status_str': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team_key, status),
                'playoff_status_str': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team_key, status),
                'overall_status_str': EventTeamStatusHelper.generate_team_at_event_status_string(team_key, status),
            })

        status_json = json.dumps(status)

        deferred.defer(
            cls._put_data,
            'event_teams/{}/{}/status'.format(event_key, team_key),
            status_json,
            _queue="firebase")

    @classmethod
    def update_live_events(cls):
        """
        Updates live_events
        """
        week_events = EventHelper.getWeekEvents()
        events_by_key = {}
        live_events = []
        for event in week_events:
            if event.now:
                events_by_key[event.key.id()] = EventConverter.convert(event, 3)
            if event.within_a_day:
                live_events.append(event)

        # Add in the Fake TBA BlueZone event (watch for circular imports)
        from helpers.bluezone_helper import BlueZoneHelper
        bluezone_event = BlueZoneHelper.update_bluezone(live_events)
        if bluezone_event:
            events_by_key[bluezone_event.key.id()] = EventConverter.convert(bluezone_event, 3)

        live_events_json = json.dumps(events_by_key)

        deferred.defer(
            cls._put_data,
            'live_events',
            live_events_json,
            _queue="firebase")

    @classmethod
    def update_event(cls, event):
        deferred.defer(
            cls._put_data,
            'live_events/{}'.format(event.key_name),
            json.dumps(EventConverter.convert(event, 3)),
            _queue="firebase")
