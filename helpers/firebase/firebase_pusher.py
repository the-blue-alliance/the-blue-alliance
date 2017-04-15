import datetime
import json
import logging
import tba_config
import traceback

from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from controllers.apiv3.model_properties import filter_match_properties
from database.dict_converters.match_converter import MatchConverter
from database.dict_converters.event_converter import EventConverter
from database.dict_converters.event_details_converter import EventDetailsConverter
from helpers.event_helper import EventHelper
from helpers.webcast_online_helper import WebcastOnlineHelper
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
    def _patch_data(cls, key, data_json):
        """
        Write or replace data to a defined path, like messages/users/user1/<data>
        """
        if not tba_config.CONFIG['firebase-push']:
            return
        secret = cls._get_secret()
        if secret is None:
            return
        url = tba_config.CONFIG['firebase-url'].format(key, secret)
        result = urlfetch.fetch(url, payload=data_json, method='PATCH', deadline=10)
        if result.status_code not in {200, 204}:
            raise Exception("Error with PATCH data to Firebase: {}; {}. ERROR {}: {}".format(url, data_json, result.status_code, result.content))

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
        if result.status_code not in {200, 204}:
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
        if result.status_code not in {200, 204}:
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

        # for team_key_name in match.team_key_names:
        #     deferred.defer(
        #     cls._delete_data,
        #     'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
        #     _queue="firebase")

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
            cls._patch_data,
            'events/{}/matches/{}'.format(match.event.id(), match.key.id()),
            match_data_json,
            _queue="firebase")

        try:
            cls.update_champ_numbers(match)
        except Exception, exception:
            logging.warning("Update champ numbers failed: {}".format(exception))
            logging.warning(traceback.format_exc())

        # for team_key_name in match.team_key_names:
        #     deferred.defer(
        #         cls._put_data,
        #         'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
        #         match_data_json,
        #         _queue="firebase")

    @classmethod
    def update_event_details(cls, event_details):
        """
        Updates an event_detail in an event
        """
        if int(event_details.key.id()[:4]) < 2017:
            return

        event_details_json = json.dumps(EventDetailsConverter.convert(event_details, 3))

        deferred.defer(
            cls._patch_data,
            'events/{}/details'.format(event_details.key.id()),
            event_details_json,
            _queue="firebase")

    @classmethod
    def update_event_team_status(cls, event_key, team_key, status):
        """
        Updates an event team status
        """
        return
        # if int(event_key[:4]) < 2017:
        #     return

        # from helpers.event_team_status_helper import EventTeamStatusHelper  # Prevent circular import

        # if status:
        #     status.update({
        #         'alliance_status_str': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team_key, status),
        #         'playoff_status_str': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team_key, status),
        #         'overall_status_str': EventTeamStatusHelper.generate_team_at_event_status_string(team_key, status),
        #     })

        # status_json = json.dumps(status)

        # deferred.defer(
        #     cls._put_data,
        #     'event_teams/{}/{}/status'.format(event_key, team_key),
        #     status_json,
        #     _queue="firebase")

    @classmethod
    def update_live_events(cls):
        """
        Updates live_events and special webcasts
        """
        events_by_key = {}
        for event_key, event in cls._update_live_events_helper().items():
            converted_event = EventConverter.convert(event, 3)
            # Only what's needed to render webcast
            partial_event = {key: converted_event[key] for key in ['key', 'name', 'short_name', 'webcasts']}
            # Hack in district code
            if event.district_key and partial_event.get('short_name'):
                partial_event['short_name'] = '[{}] {}'.format(event.district_key.id()[4:].upper(), partial_event['short_name'])

            events_by_key[event_key] = partial_event

        deferred.defer(
            cls._put_data,
            'live_events',
            json.dumps(events_by_key),
            _queue="firebase")

        deferred.defer(
            cls._put_data,
            'special_webcasts',
            json.dumps(cls.get_special_webcasts()),
            _queue="firebase")

    @classmethod
    @ndb.toplevel
    def _update_live_events_helper(cls):
        week_events = EventHelper.getWeekEvents()
        events_by_key = {}
        live_events = []
        for event in week_events:
            if event.now:
                event._webcast = event.current_webcasts  # Only show current webcasts
                for webcast in event.webcast:
                    WebcastOnlineHelper.add_online_status_async(webcast)
                events_by_key[event.key.id()] = event
            if event.within_a_day:
                live_events.append(event)

        # Add in the Fake TBA BlueZone event (watch for circular imports)
        from helpers.bluezone_helper import BlueZoneHelper
        bluezone_event = BlueZoneHelper.update_bluezone(live_events)
        if bluezone_event:
            for webcast in bluezone_event.webcast:
                WebcastOnlineHelper.add_online_status_async(webcast)
            events_by_key[bluezone_event.key_name] = bluezone_event

        return events_by_key

    @classmethod
    @ndb.toplevel
    def get_special_webcasts(cls):  # TODO: Break this out of FirebasePusher 2017-03-01 -fangeugene
        special_webcasts_temp = Sitevar.get_by_id('gameday.special_webcasts')
        if special_webcasts_temp:
            special_webcasts_temp = special_webcasts_temp.contents.get('webcasts', [])
        else:
            special_webcasts_temp = []

        special_webcasts = []
        for webcast in special_webcasts_temp:
            WebcastOnlineHelper.add_online_status_async(webcast)
            special_webcasts.append(webcast)

        return special_webcasts

    @classmethod
    def update_event(cls, event):
        WebcastOnlineHelper.add_online_status(event.webcast)

        converted_event = EventConverter.convert(event, 3)
        deferred.defer(
            cls._patch_data,
            'live_events/{}'.format(event.key_name),
            json.dumps({key: converted_event[key] for key in ['key', 'name', 'short_name', 'webcasts']}),
            _queue="firebase")

    @classmethod
    @ndb.transactional
    def update_champ_numbers(cls, match):
        champ_numbers_sitevar = Sitevar.get_or_insert(
            'champ_numbers',
            values_json=json.dumps({
                'kpa_accumulated': 0,
                'rotors_engaged': 0,
                'ready_for_takeoff': 0,
            }))

        old_contents = champ_numbers_sitevar.contents
        for color in ['red', 'blue']:
            old_contents['kpa_accumulated'] += match.score_breakdown[color]['autoFuelPoints'] + match.score_breakdown[color]['teleopFuelPoints']
            if match.score_breakdown[color]['rotor4Engaged']:
                old_contents['rotors_engaged'] += 4
            elif match.score_breakdown[color]['rotor3Engaged']:
                old_contents['rotors_engaged'] += 3
            elif match.score_breakdown[color]['rotor2Engaged']:
                old_contents['rotors_engaged'] += 2
            elif match.score_breakdown[color]['rotor1Engaged']:
                old_contents['rotors_engaged'] += 1
            old_contents['ready_for_takeoff'] += match.score_breakdown[color]['teleopTakeoffPoints'] / 50

        champ_numbers_sitevar.contents = old_contents
        champ_numbers_sitevar.put()

        deferred.defer(
            cls._patch_data,
            'champ_numbers',
            json.dumps(old_contents),
            _queue="firebase")
