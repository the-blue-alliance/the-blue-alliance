import logging
import re

from google.appengine.api import memcache
from google.appengine.api import urlfetch

import tba_config

from datafeeds.datafeed_usfirst import DatafeedUsfirst
from datafeeds.usfirst_legacy_event_details_parser import UsfirstLegacyEventDetailsParser
from datafeeds.usfirst_legacy_event_teams_parser import UsfirstLegacyEventTeamsParser
from datafeeds.usfirst_legacy_team_details_parser import UsfirstLegacyTeamDetailsParser

from helpers.event_helper import EventHelper

from models.event import Event
from models.team import Team


class DatafeedUsfirstLegacy(DatafeedUsfirst):
    SESSION_KEY_GENERATING_PATTERN = "https://my.usfirst.org/myarea/index.lasso?event_type=FRC&year=%s"  # % (year)

    EVENT_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_details&eid=%s"
    EVENT_TEAMS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=event_teamlist&results_size=250&eid=%s"
    TEAM_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=team_details&tpid=%s"

    def __init__(self, *args, **kw):
        self._session_key = {}
        super(DatafeedUsfirstLegacy, self).__init__(*args, **kw)

    def getSessionKey(self, year):
        """
        Grab a page from FIRST so we can get a session key out the response header.
        """
        year = int(year)

        if self._session_key.get(year, False):
            return self._session_key.get(year)

        memcache_key = "usfirst_session_key_%s" % year
        session_key = memcache.get(memcache_key)
        if session_key is not None:
            self._session_key[year] = session_key
            return self._session_key.get(year)

        url = self.SESSION_KEY_GENERATING_PATTERN % year
        try:
            result = urlfetch.fetch(
                url, headers={'Referer': 'usfirst.org'}, deadline=10)
        except Exception, e:
            logging.error("URLFetch failed for: {}".format(url))
            logging.info(e)

            session_key = ''
            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, session_key, 60 * 5)
            self._session_key[year] = session_key
            return session_key

        if result.status_code == 200:
            session_key = result.headers.get('Set-Cookie', None)
            if session_key is not None:
                if tba_config.CONFIG["memcache"]:
                    memcache.set(memcache_key, session_key, 60 * 5)
                self._session_key[year] = session_key
                return self._session_key[year]
            logging.error('Unable to get USFIRST session key for %s.' % year)
            return None
        else:
            logging.error('HTTP code %s. Unable to retreive url: %s' %
                          (result.status_code,
                           self.SESSION_KEY_GENERATING_PATTERN))

    def getEventDetails(self, year, first_eid):
        if type(year) is not int:
            raise TypeError("year must be an integer")
        url = self.EVENT_DETAILS_URL_PATTERN % (first_eid)
        event, _ = self.parse(url, UsfirstLegacyEventDetailsParser,
                              self.getSessionKey(year))
        if event is None:
            return None

        return Event(
            id=str(event["year"]) + str.lower(str(event["event_short"])),
            end_date=event.get("end_date", None),
            event_short=event.get("event_short", None),
            event_type_enum=event.get("event_type_enum", None),
            first_eid=first_eid,
            name=event.get("name", None),
            short_name=event.get("short_name", None),
            official=True,
            start_date=event.get("start_date", None),
            venue_address=event.get("venue_address", None),
            location=event.get("location", None),
            timezone_id=EventHelper.get_timezone_id(
                event.get("location", None), '{}{}'.format(
                    event['year'], event['event_short'])),
            website=event.get("website", None),
            year=event.get("year", None))

    def getEventTeams(self, year, first_eid):
        """
        Returns a list of team_numbers attending a particular Event
        """
        if type(year) is not int:
            raise TypeError("year must be an integer")
        url = self.EVENT_TEAMS_URL_PATTERN % (first_eid)
        teams, _ = self.parse(url, UsfirstLegacyEventTeamsParser,
                              self.getSessionKey(year))
        if teams is None:
            return None

        return [
            Team(
                id="frc%s" % team.get("team_number", None),
                first_tpid=team.get("first_tpid", None),
                first_tpid_year=year,
                team_number=team.get("team_number", None)) for team in teams
        ]

    def getTeamDetails(self, team):
        if hasattr(team, 'first_tpid'):
            if team.first_tpid:
                url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid)
                team_dict, _ = self.parse(url, UsfirstLegacyTeamDetailsParser,
                                          self.getSessionKey(
                                              team.first_tpid_year))

                if team_dict is not None and "team_number" in team_dict:
                    return Team(
                        id="frc%s" % team_dict.get("team_number", None),
                        team_number=team_dict.get("team_number", None),
                        name=self._shorten(team_dict.get("name", None)),
                        address=team_dict.get("address", None),
                        nickname=team_dict.get("nickname", None),
                        website=team_dict.get("website", None),
                        rookie_year=team_dict.get("rookie_year", None),
                    )
                else:
                    logging.warning(
                        "No team_number found scraping %s, probably retired team"
                        % team.team_number)
                    return None

        logging.warning('Null TPID for team %s' % team.team_number)
        return None
