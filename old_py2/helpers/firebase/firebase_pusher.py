import datetime
import json
import logging
import tba_config
import traceback

from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from consts.event_type import EventType
from database.dict_converters.match_converter import MatchConverter
from database.dict_converters.event_converter import EventConverter
from database.dict_converters.event_details_converter import EventDetailsConverter
from database.match_query import EventMatchesQuery
from helpers.event_helper import EventHelper
from helpers.webcast_online_helper import WebcastOnlineHelper
from models.event import Event
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
            'e/{}/m/{}'.format(match.event.id(), match.short_key),
            _queue="firebase",
            _url='/_ah/queue/deferred_firebase_delete_match'
        )

        # for team_key_name in match.team_key_names:
        #     deferred.defer(
        #     cls._delete_data,
        #     'event_teams/{}/{}/matches/{}'.format(match.event.id(), team_key_name, match.key.id()),
        #     _queue="firebase")

    @classmethod
    def _construct_match_dict(cls, match):
        """
        Minimal amount needed to render
        """
        match_dict = {
            'c': match['comp_level'],
            's': match['set_number'],
            'm': match['match_number'],
            'r': match['alliances']['red']['score'],
            'rt': match['alliances']['red']['team_keys'],
            'b': match['alliances']['blue']['score'],
            'bt': match['alliances']['blue']['team_keys'],
            't': match['time'],
            'pt': match['predicted_time'],
            'w': match['winning_alliance'],
        }
        return match_dict

    @classmethod
    def replace_event_matches(cls, event_key, matches):
        """
        Deletes matches from an event and puts these instead
        """

        match_data = {}
        for match in matches:
            match_data[match.short_key] = cls._construct_match_dict(MatchConverter.convert(match, 3))
        deferred.defer(
            cls._put_data,
            'e/{}/m'.format(event_key),
            json.dumps(match_data),
            _queue="firebase",
            _url='/_ah/queue/deferred_firebase_replace_event_matches'
        )

    @classmethod
    def update_match(cls, match, updated_attrs):
        """
        Updates a match in an event and event/team
        """
        if match.year < 2017:
            return

        if 'predicted_time' in updated_attrs:
            # Hacky way of preventing predicted time updates from clobbering scores
            match_dict = {
                'pt': MatchConverter.convert(match, 3)['predicted_time'],
            }
        else:
            match_dict = cls._construct_match_dict(MatchConverter.convert(match, 3))

        deferred.defer(
            cls._patch_data,
            'e/{}/m/{}'.format(match.event.id(), match.short_key),
            json.dumps(match_dict),
            _queue="firebase",
            _url='/_ah/queue/deferred_firebase_update_match'
        )

        try:
            if match.event.get().event_type_enum in EventType.CMP_EVENT_TYPES:
                cls.update_champ_numbers()
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
        return
        # if int(event_details.key.id()[:4]) < 2017:
        #     return

        # event_details_json = json.dumps(EventDetailsConverter.convert(event_details, 3))

        # deferred.defer(
        #     cls._patch_data,
        #     'events/{}/details'.format(event_details.key.id()),
        #     event_details_json,
        #     _queue="firebase")

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
            _queue="firebase",
            _url='/_ah/queue/deferred_firebase_update_live_events'
        )

        deferred.defer(
            cls._put_data,
            'special_webcasts',
            json.dumps(cls.get_special_webcasts()),
            _queue="firebase",
            _url='/_ah/queue/deferred_firebase_update_special_webcasts'
        )

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

        # To get Champ events to show up before they are actually going on
        forced_live_events = Sitevar.get_or_insert(
            'forced_live_events',
            values_json=json.dumps([]))
        for event in ndb.get_multi([ndb.Key('Event', ekey) for ekey in forced_live_events.contents]):
            if event.webcast:
                for webcast in event.webcast:
                    WebcastOnlineHelper.add_online_status_async(webcast)
            events_by_key[event.key.id()] = event

        # # Add in the Fake TBA BlueZone event (watch for circular imports)
        # from helpers.bluezone_helper import BlueZoneHelper
        # bluezone_event = BlueZoneHelper.update_bluezone(live_events)
        # if bluezone_event:
        #     for webcast in bluezone_event.webcast:
        #         WebcastOnlineHelper.add_online_status_async(webcast)
        #     events_by_key[bluezone_event.key_name] = bluezone_event

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
            _queue="firebase",
            _url='/_ah/queue/deferred_firebase_update_event'
        )

    @classmethod
    def update_champ_numbers(cls):
        events = Event.query(
            Event.year==2017,
            Event.event_type_enum.IN([
                EventType.CMP_DIVISION,
                EventType.CMP_FINALS])).fetch()
        matches_futures = []
        for event in events:
            matches_futures.append(EventMatchesQuery(event.key.id()).fetch_async())

        pressure = 0
        rotors = 0
        climbs = 0
        for matches_future in matches_futures:
            for match in matches_future.get_result():
                if not match.has_been_played:
                    continue
                for color in ['red', 'blue']:
                    pressure += match.score_breakdown[color]['autoFuelPoints'] + match.score_breakdown[color]['teleopFuelPoints']
                    if match.score_breakdown[color]['rotor4Engaged']:
                        rotors += 4
                    elif match.score_breakdown[color]['rotor3Engaged']:
                        rotors += 3
                    elif match.score_breakdown[color]['rotor2Engaged']:
                        rotors += 2
                    elif match.score_breakdown[color]['rotor1Engaged']:
                        rotors += 1
                    climbs += match.score_breakdown[color]['teleopTakeoffPoints'] / 50

        deferred.defer(
            cls._patch_data,
            'champ_numbers',
            json.dumps({
                'kpa_accumulated': pressure,
                'rotors_engaged': rotors,
                'ready_for_takeoff': climbs,
            }),
            _queue="firebase")
