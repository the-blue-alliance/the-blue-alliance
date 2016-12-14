import json
import logging
import re
import urllib

from google.appengine.api import memcache, urlfetch
from google.appengine.ext import ndb

from models.sitevar import Sitevar


class LocationHelper(object):
    @classmethod
    def get_event_lat_lon(cls, event):
        """
        Try different combinations of venue, address, and location to
        get latitude and longitude for an event
        """
        lat_lon, _ = cls.get_lat_lon(event.venue_address_safe)
        if not lat_lon:
            lat_lon, _ = cls.get_lat_lon(u'{} {}'.format(event.venue, event.location))
        if not lat_lon:
            lat_lon, _ = cls.get_lat_lon(event.location)
        if not lat_lon:
            lat_lon, _ = cls.get_lat_lon(u'{} {}'.format(event.city, event.country))
        if not lat_lon:
            logging.warning("Finding Lat/Lon for event {} failed!".format(event.key_name))
        return lat_lon

    @classmethod
    def get_team_lat_lon(cls, team):
        """
        Try different combinations of team name (which should include high
        school or main sponsor) and team location to get latitude and longitude
        for a team
        """
        if team.name:
            split_name = re.split('/|&', team.name)  # Guessing sponsors/school by splitting name by '/' or '&'
        else:
            split_name = None

        best_lat_lon = None
        least_num_results = float('inf')
        if split_name:
            futures = []
            for possible_location in [split_name[-1], split_name[0]]:
                # Try to locate team. Usually first or last entries are best candidates, with last being the priority
                futures.append(cls.get_lat_lon_async(u'{} {}'.format(possible_location, team.location)))

            for future in futures:
                lat_lon, num_results = future.get_result()
                if lat_lon and num_results < least_num_results:  # Fewer results is less ambiguous and more likely to be correct
                    best_lat_lon = lat_lon
                    least_num_results = num_results
        if not best_lat_lon:
            best_lat_lon, _ = cls.get_lat_lon(team.location)
        if not best_lat_lon:
            logging.warning("Finding Lat/Lon for team {} failed!".format(team.key.id()))
        return best_lat_lon

    @classmethod
    def get_lat_lon(cls, location, geocode=False):
        return cls.get_lat_lon_async(location, geocode=geocode).get_result()

    @classmethod
    @ndb.tasklet
    def get_lat_lon_async(cls, location, geocode=False):
        cache_key = u'get_lat_lon_{}'.format(location)
        result = memcache.get(cache_key)
        if not result:
            context = ndb.get_context()
            lat_lon = None
            num_results = 0

            if not location:
                raise ndb.Return(lat_lon, num_results)

            location = location.encode('utf-8')

            google_secrets = Sitevar.get_by_id("google.secrets")
            google_api_key = None
            if google_secrets is None:
                logging.warning("Missing sitevar: google.api_key. API calls rate limited by IP and may be over rate limit.")
            else:
                google_api_key = google_secrets.contents['api_key']

            # textsearch request
            if google_api_key and not geocode:
                textsearch_params = {
                    'query': location,
                    'key': google_api_key,
                }
                textsearch_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?%s' % urllib.urlencode(textsearch_params)
                try:
                    textsearch_result = yield context.urlfetch(textsearch_url)
                    if textsearch_result.status_code == 200:
                        textsearch_dict = json.loads(textsearch_result.content)
                        if textsearch_dict['status'] == 'ZERO_RESULTS':
                            logging.info('No textsearch results for location: {}'.format(location))
                        elif textsearch_dict['status'] == 'OK':
                            lat_lon = textsearch_dict['results'][0]['geometry']['location']['lat'], textsearch_dict['results'][0]['geometry']['location']['lng']
                            num_results = len(textsearch_dict['results'])
                        else:
                            logging.warning('Textsearch failed!')
                            logging.warning(textsearch_dict)
                    else:
                        logging.warning('Textsearch failed with url {}.'.format(textsearch_url))
                        logging.warning(textsearch_dict)
                except Exception, e:
                    logging.warning('urlfetch for textsearch request failed with url {}.'.format(textsearch_url))
                    logging.warning(e)
            else:
                # Fallback to geocode request
                geocode_params = {
                    'address': location,
                    'sensor': 'false',
                }
                if google_api_key:
                    geocode_params['key'] = google_api_key
                geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?%s' % urllib.urlencode(geocode_params)
                try:
                    geocode_result = yield context.urlfetch(geocode_url)
                    if geocode_result.status_code == 200:
                        geocode_dict = json.loads(geocode_result.content)
                        if geocode_dict['status'] == 'ZERO_RESULTS':
                            logging.info('No geocode results for location: {}'.format(location))
                        elif geocode_dict['status'] == 'OK':
                            lat_lon = geocode_dict['results'][0]['geometry']['location']['lat'], geocode_dict['results'][0]['geometry']['location']['lng']
                            num_results = len(geocode_dict['results'])
                        else:
                            logging.warning('Geocoding failed!')
                            logging.warning(geocode_dict)
                    else:
                        logging.warning('Geocoding failed with url {}.'.format(geocode_url))
                except Exception, e:
                    logging.warning('urlfetch for geocode request failed with url {}.'.format(geocode_url))
                    logging.warning(e)

            result = lat_lon, num_results
            memcache.set(cache_key, result)

        raise ndb.Return(result)

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
