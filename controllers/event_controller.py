import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandlerFB, CacheableHandler
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.datastore_cache_helper import DatastoreCache
from helpers.team_helper import TeamHelper
from helpers.event_helper import EventHelper

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class EventList(CacheableHandler):
    """
    List all Events.
    """

    VALID_YEARS = [2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002]

    def __init__(self, *args, **kw):
        super(EventList, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._cache_key = "event_list_{}_{}" # (year, explicit_year)
        self._cache_version = 4

    def get(self, year=None, explicit_year=False):
        if year == '':
            return self.redirect("/events")

        if year:
            if not year.isdigit():
                return self.redirect("/error/404")
            year = int(year)
            if year not in self.VALID_YEARS:
                return self.redirect("/error/404")
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False

        self._cache_key = self._cache_key.format(year, explicit_year)
        super(EventList, self).get(year, explicit_year)
        
    def _render(self, year=None, explicit_year=False):
        event_keys = Event.query(Event.year == year).fetch(1000, keys_only=True)
        events = ndb.get_multi(event_keys)
        events.sort(key=EventHelper.distantFutureIfNoStartDate)

        week_events = None
        if year >= 2005:
            week_events = EventHelper.groupByWeek(events)
    
        template_values = {
            "events": events,
            "explicit_year": explicit_year,
            "selected_year": year,
            "valid_years": self.VALID_YEARS,
            "week_events": week_events,
        }
    
        path = os.path.join(os.path.dirname(__file__), '../templates/event_list.html')
        return template.render(path, template_values)

    def cacheFlush(self):
        year = datetime.datetime.now().year
        keys = [self.cache_key.format(year, True), self.cache_key.format(year, False)]
        memcache.delete_multi_async(keys)
        DatastoreCache.delete_multi_async(keys)
        return keys


class EventDetail(CacheableHandler):
    """
    Show an Event.
    event_code like "2010ct"
    """

    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(EventDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "event_detail_{}" # (event_key)
        self._cache_version = 3

    def get(self, event_key):
        if not event_key:
            return self.redirect("/events")

        self._cache_key = self._cache_key.format(event_key)
        super(EventDetail, self).get(event_key)

    def _render(self, event_key):
        event = Event.get_by_id(event_key)
        
        if not event:
            return self.redirect("/error/404")
          
        event.prepAwardsMatchesTeams()

        awards = AwardHelper.organizeAwards(event.awards)
        cleaned_matches = MatchHelper.deleteInvalidMatches(event.matches)
        matches = MatchHelper.organizeMatches(cleaned_matches)
        teams = TeamHelper.sortTeams(event.teams)
        
        num_teams = len(teams)
        middle_value = num_teams/2
        if num_teams%2 != 0:
            middle_value += 1
        teams_a, teams_b = teams[:middle_value], teams[middle_value:]
        
        oprs = sorted(zip(event.oprs,event.opr_teams), reverse=True) # sort by OPR
        oprs = oprs[:14] # get the top 15 OPRs

        if event.within_a_day:
            matches_recent = MatchHelper.recentMatches(cleaned_matches)
            matches_upcoming = MatchHelper.upcomingMatches(cleaned_matches)
        else:
            matches_recent = None
            matches_upcoming = None

        bracket_table = {}
        qf_matches = matches['qf']
        sf_matches = matches['sf']
        f_matches = matches['f']
        if qf_matches:
            bracket_table['qf'] = MatchHelper.generateBracket(qf_matches)
        if sf_matches:
            bracket_table['sf'] = MatchHelper.generateBracket(sf_matches)
        if f_matches:
            bracket_table['f'] = MatchHelper.generateBracket(f_matches)
            
        template_values = {
            "event": event,
            "matches": matches,
            "matches_recent": matches_recent,
            "matches_upcoming": matches_upcoming,
            "awards": awards,
            "teams_a": teams_a,
            "teams_b": teams_b,
            "num_teams": num_teams,
            "oprs": oprs,
            "bracket_table": bracket_table,
        }

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION
            
        path = os.path.join(os.path.dirname(__file__), '../templates/event_details.html')
        return template.render(path, template_values)


class EventRss(CacheableHandler):
    """
    Generates a RSS feed for the matches in a event
    """
    def __init__(self, *args, **kw):
        super(EventRss, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5
        self._cache_key = "event_rss_{}" # (event_key)
        self._cache_version = 2

    def get(self, event_key):
        if not event_key:
            return self.redirect("/events")

        self._cache_key = self._cache_key.format(event_key)
        super(EventRss, self).get(event_key)

    def _render(self, event_key):
        event = Event.get_by_id(event_key)
        if not event:
            return self.redirect("/error/404")

        matches = MatchHelper.organizeMatches(event.matches)
    
        template_values = {
                "event": event,
                "matches": matches,
                "datetime": datetime.datetime.now()
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/event_rss.xml')
        self.response.headers.add_header('content-type', 'application/xml', charset='utf-8')
        return template.render(path, template_values)
