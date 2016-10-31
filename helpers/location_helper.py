import json
import logging
import re
import tba_config
import urllib

from google.appengine.api import memcache, urlfetch
from google.appengine.ext import ndb

from models.sitevar import Sitevar


GOOGLE_SECRETS = Sitevar.get_by_id("google.secrets")
GOOGLE_API_KEY = None
if GOOGLE_SECRETS is None:
    logging.warning("Missing sitevar: google.api_key. API calls rate limited by IP and may be over rate limit.")
else:
    GOOGLE_API_KEY = GOOGLE_SECRETS.contents['api_key']


class LocationHelper(object):
    # @classmethod
    # def get_event_lat_lon(cls, event):
    #     """
    #     Try different combinations of venue, address, and location to
    #     get latitude and longitude for an event
    #     """
    #     lat_lon, _ = cls.get_lat_lon(event.venue_address_safe)
    #     if not lat_lon:
    #         lat_lon, _ = cls.get_lat_lon(u'{} {}'.format(event.venue, event.location))
    #     if not lat_lon:
    #         lat_lon, _ = cls.get_lat_lon(event.location)
    #     if not lat_lon:
    #         lat_lon, _ = cls.get_lat_lon(u'{} {}'.format(event.city, event.country))
    #     if not lat_lon:
    #         logging.warning("Finding Lat/Lon for event {} failed!".format(event.key_name))
    #     return lat_lon

    # @classmethod
    # def get_team_lat_lon(cls, team):
    #     """
    #     Try different combinations of team name (which should include high
    #     school or main sponsor) and team location to get latitude and longitude
    #     for a team
    #     """
    #     if team.name:
    #         split_name = re.split('/|&', team.name)  # Guessing sponsors/school by splitting name by '/' or '&'
    #     else:
    #         split_name = None

    #     best_lat_lon = None
    #     least_num_results = float('inf')
    #     if split_name:
    #         futures = []
    #         for possible_location in [split_name[-1], split_name[0]]:
    #             # Try to locate team. Usually first or last entries are best candidates, with last being the priority
    #             futures.append(cls.get_lat_lon_async(u'{} {}'.format(possible_location, team.location)))

    #         for future in futures:
    #             lat_lon, num_results = future.get_result()
    #             if lat_lon and num_results < least_num_results:  # Fewer results is less ambiguous and more likely to be correct
    #                 best_lat_lon = lat_lon
    #                 least_num_results = num_results
    #     if not best_lat_lon:
    #         best_lat_lon, _ = cls.get_lat_lon(team.location)
    #     if not best_lat_lon:
    #         logging.warning("Finding Lat/Lon for team {} failed!".format(team.key.id()))
    #     return best_lat_lon

    @classmethod
    def get_team_location_info(cls, team):
        """
        Search for different combinations of team name (which should include
        high school or title sponsor) with city, state_prov, postalcode, and country
        in attempt to find the correct place associated with the team.
        """
        if not team.location:
            return {}

        # Find possible schools/title sponsors
        possible_names = []
        MAX_SPLIT = 3  # Filters out long names that are unlikely
        if team.name:
            # Guessing sponsors/school by splitting name by '/' or '&'
            split1 = re.split('&', team.name)
            split2 = re.split('/', team.name)
            if split1 and \
                    split1[-1].count('&') < MAX_SPLIT and split1[-1].count('/') < MAX_SPLIT:
                possible_names.append(split1[-1])
            if split2 and split2[-1] not in possible_names and \
                     split2[-1].count('&') < MAX_SPLIT and split2[-1].count('/') < MAX_SPLIT:
                possible_names.append(split2[-1])
            if split1 and split1[0] not in possible_names and \
                     split1[0].count('&') < MAX_SPLIT and split1[0].count('/') < MAX_SPLIT:
                possible_names.append(split1[0])
            if split2 and split2[0] not in possible_names and \
                     split2[0].count('&') < MAX_SPLIT and split2[0].count('/') < MAX_SPLIT:
                possible_names.append(split2[0])

        # Construct possible queries based on name and location. Order matters.
        possible_queries = []
        for possible_name in possible_names:
            for query in [possible_name, u'{} {}'.format(possible_name, team.location)]:
                possible_queries.append(query)

        # Try to find place based on possible queries
        best_score = 0
        best_location_info = {}
        textsearch_results_candidates = []  # More trustworthy candidates are added first
        for query in possible_queries:
            textsearch_results = cls.google_maps_textsearch_async(query).get_result()
            if textsearch_results:
                if len(textsearch_results) == 1:
                    location_info = cls.construct_location_info_async(textsearch_results[0]).get_result()
                    score = cls.compute_team_location_score(team, location_info)
                    if score == 1:
                        # Very likely to be correct if only 1 result and as a perfect score
                        return location_info
                    elif score > best_score:
                        # Only 1 result but score is imperfect
                        best_score = score
                        best_location_info = location_info
                else:
                    # Save queries with multiple results for later evaluation
                    textsearch_results_candidates.append(textsearch_results)

        # Check if we have found anything reasonable
        if best_location_info and best_score > 0.5:
            return best_location_info

        # Try to find place using only location
        if not textsearch_results_candidates:
            textsearch_results = cls.google_maps_textsearch_async(team.location).get_result()
            if textsearch_results:
                textsearch_results_candidates.append(textsearch_results)

        # Try to find place using only city, country
        if not textsearch_results_candidates and team.city and team.country:
            textsearch_results = cls.google_maps_textsearch_async(u'{} {}'.format(team.city, team.country)).get_result()
            if textsearch_results:
                textsearch_results_candidates.append(textsearch_results)

        if not textsearch_results_candidates:
            logging.warning("Finding textsearch results for team {} failed!".format(team.key.id()))
            return {}

        # Consider all candidates and find best one
        for textsearch_results in textsearch_results_candidates:
            for textsearch_result in textsearch_results:
                location_info = cls.construct_location_info_async(textsearch_result).get_result()
                score = cls.compute_team_location_score(team, location_info)
                if score == 1:
                    return location_info
                elif score > best_score:
                    best_score = score
                    best_location_info = location_info

        return best_location_info

    @classmethod
    def compute_team_location_score(cls, team, location_info):
        """
        Score for correctness. 1.0 is perfect.
        Not checking for absolute equality in case of existing data errors.
        Check with both long and short names
        """
        max_score = 4.0
        score = 0.0
        if team.country and location_info.get('country', None) and \
                (team.country.lower() in location_info['country'].lower() or
                location_info['country'].lower() in team.country.lower() or
                team.country.lower() in location_info['country_short'].lower() or
                location_info['country_short'].lower() in team.country.lower()):
            score += 1
            print 1
        if team.state_prov and location_info.get('state_prov', None) and \
                (team.state_prov.lower() in location_info['state_prov'].lower() or
                location_info['state_prov'].lower() in team.state_prov.lower() or
                team.state_prov.lower() in location_info['state_prov_short'].lower() or
                location_info['state_prov_short'].lower() in team.state_prov.lower()):
            score += 1
            print 2
        if team.city and location_info.get('city', None) and \
                (team.city.lower() in location_info['city'].lower() or
                location_info['city'].lower() in team.city.lower()):
            score += 1
            print 3
        if team.postalcode and location_info.get('postal_code', None) and \
                (team.postalcode.lower() in location_info['postal_code'].lower() or
                location_info['postal_code'].lower() in team.postalcode.lower()):
            # If postal code is right and anything else is right, the confidence is very high
            score += 3
            print 4
        print score
        return min(1.0, score / max_score)

    @classmethod
    @ndb.tasklet
    def construct_location_info_async(cls, textsearch_result):
        """
        Gets location info given a textsearch result
        """
        location_info = {
            'formatted_address': textsearch_result['formatted_address'],
            'lat': textsearch_result['geometry']['location']['lat'],
            'lng': textsearch_result['geometry']['location']['lng'],
            'name': textsearch_result['name'],
        }
        geocode_results = yield cls.google_maps_geocode_async(textsearch_result['formatted_address'])
        if geocode_results:
            for component in geocode_results[0]['address_components']:
                if 'street_number' in component['types']:
                    location_info['street_number'] = component['long_name']
                elif 'route' in component['types']:
                    location_info['street'] = component['long_name']
                elif 'locality' in component['types']:
                    location_info['city'] = component['long_name']
                elif 'administrative_area_level_1' in component['types']:
                    location_info['state_prov'] = component['long_name']
                    location_info['state_prov_short'] = component['short_name']
                elif 'country' in component['types']:
                    location_info['country'] = component['long_name']
                    location_info['country_short'] = component['short_name']
                elif 'postal_code' in component['types']:
                    location_info['postal_code'] = component['long_name']

            location_info['formatted_address'] = geocode_results[0]['formatted_address']
            location_info['lat'] = geocode_results[0]['geometry']['location']['lat']
            location_info['lng'] = geocode_results[0]['geometry']['location']['lng']
            location_info['location_type'] = geocode_results[0]['geometry']['location_type']

        raise ndb.Return(location_info)

    @classmethod
    @ndb.tasklet
    def google_maps_textsearch_async(cls, query):
        """
        https://developers.google.com/places/web-service/search#TextSearchRequests
        """
        print "TEXTSEARCH " + query.encode('ascii', 'ignore')
        if not GOOGLE_API_KEY:
            logging.warning("Must have sitevar google.api_key to use Google Maps Textsearch")
            raise ndb.Return(None)

        results = None
        if query:
            cache_key = u'google_maps_textsearch:{}'.format(query.encode('ascii', 'ignore'))
            query = query.encode('utf-8')
            results = memcache.get(cache_key)
            if not results:
                textsearch_params = {
                    'query': query,
                    'key': GOOGLE_API_KEY,
                }
                textsearch_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?%s' % urllib.urlencode(textsearch_params)
                try:
                    # Make async urlfetch call
                    rpc = urlfetch.create_rpc()
                    urlfetch.make_fetch_call(rpc, textsearch_url)
                    textsearch_result = yield rpc

                    # Parse urlfetch result
                    if textsearch_result.status_code == 200:
                        textsearch_dict = json.loads(textsearch_result.content)
                        if textsearch_dict['status'] == 'ZERO_RESULTS':
                            logging.info('No textsearch results for query: {}'.format(query))
                        elif textsearch_dict['status'] == 'OK':
                            results = textsearch_dict['results']
                        else:
                            logging.warning('Textsearch failed!')
                            logging.warning(textsearch_dict)
                    else:
                        logging.warning('Textsearch failed with url {}.'.format(textsearch_url))
                        logging.warning(textsearch_dict)
                except Exception, e:
                    logging.warning('urlfetch for textsearch request failed with url {}.'.format(textsearch_url))
                    logging.warning(e)

                if tba_config.CONFIG['memcache']:
                    memcache.set(cache_key, result)
        raise ndb.Return(results)

    @classmethod
    @ndb.tasklet
    def google_maps_geocode_async(cls, address):
        """
        https://developers.google.com/maps/documentation/geocoding/start
        """
        print "GEOCODE " + address.encode('ascii', 'ignore')
        results = None
        if address:
            cache_key = u'google_maps_geocode:{}'.format(address.encode('ascii', 'ignore'))
            address = address.encode('utf-8')
            results = memcache.get(cache_key)
            if not results:
                geocode_params = {
                    'address': address,
                    'sensor': 'false',
                }
                if GOOGLE_API_KEY:
                    geocode_params['key'] = GOOGLE_API_KEY
                geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?%s' % urllib.urlencode(geocode_params)
                try:
                    # Make async urlfetch call
                    rpc = urlfetch.create_rpc()
                    urlfetch.make_fetch_call(rpc, geocode_url)
                    geocode_result = yield rpc

                    # Parse urlfetch call
                    if geocode_result.status_code == 200:
                        geocode_dict = json.loads(geocode_result.content)
                        if geocode_dict['status'] == 'ZERO_RESULTS':
                            logging.info('No geocode results for address: {}'.format(address))
                        elif geocode_dict['status'] == 'OK':
                            results = geocode_dict['results']
                        else:
                            logging.warning('Geocoding failed!')
                            logging.warning(geocode_dict)
                    else:
                        logging.warning('Geocoding failed with url {}.'.format(geocode_url))
                except Exception, e:
                    logging.warning('urlfetch for geocode request failed with url {}.'.format(geocode_url))
                    logging.warning(e)

                if tba_config.CONFIG['memcache']:
                    memcache.set(cache_key, result)
        raise ndb.Return(results)

    @classmethod
    def get_timezone_id(cls, location, lat_lon=None):
        if lat_lon is None:
            result, _ = cls.get_lat_lon(location)
            if result is None:
                return None
            else:
                lat, lng = result
        else:
            lat, lng = lat_lon

        google_secrets = Sitevar.get_by_id("google.secrets")
        google_api_key = None
        if google_secrets is None:
            logging.warning("Missing sitevar: google.api_key. API calls rate limited by IP and may be over rate limit.")
        else:
            google_api_key = google_secrets.contents['api_key']

        # timezone request
        tz_params = {
            'location': '%s,%s' % (lat, lng),
            'timestamp': 0,  # we only care about timeZoneId, which doesn't depend on timestamp
            'sensor': 'false',
        }
        if google_api_key is not None:
            tz_params['key'] = google_api_key
        tz_url = 'https://maps.googleapis.com/maps/api/timezone/json?%s' % urllib.urlencode(tz_params)
        try:
            tz_result = urlfetch.fetch(tz_url)
        except Exception, e:
            logging.warning('urlfetch for timezone request failed: {}'.format(tz_url))
            logging.info(e)
            return None
        if tz_result.status_code != 200:
            logging.warning('TZ lookup for (lat, lng) failed! ({}, {})'.format(lat, lng))
            return None
        tz_dict = json.loads(tz_result.content)
        if 'timeZoneId' not in tz_dict:
            logging.warning('No timeZoneId for (lat, lng)'.format(lat, lng))
            return None
        return tz_dict['timeZoneId']
