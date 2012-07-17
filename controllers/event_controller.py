import datetime
import os
import logging
import PyRSS2Gen

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

import tba_config
from models import Event, Match, EventTeam, Team
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamHelper

class EventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self, year=None):
        if year:
            year = int(year)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False
        
        memcache_key = "event_list_%s" % year
        html = memcache.get(memcache_key)
        
        if html is None:
            events = Event.all().filter("year =", int(year)).order('start_date').fetch(1000)
        
            template_values = {
                "explicit_year": explicit_year,
                "year": year,
                "events": events,
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/event_list.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 3600) 
        
        self.response.out.write(html)
        
class EventDetail(webapp.RequestHandler):
    """
    Show an Event.
    event_code like "2010ct"
    """
    def get(self, event_key):
        memcache_key = "event_detail_%s" % event_key
        html = memcache.get(memcache_key)
        
        if html is None:
            event = Event.get_by_key_name(event_key)
            matches = MatchHelper.organizeMatches(event.match_set)
            
            team_keys = [EventTeam.team.get_value_for_datastore(event_team).name() for event_team in event.teams.fetch(500)]
            teams = Team.get_by_key_name(team_keys)
            teams = TeamHelper.sortTeams(teams)

            num_teams = len(teams)
            middle_value = num_teams/2
            if num_teams%2 != 0:
                middle_value += 1
            teams_a, teams_b = teams[:middle_value], teams[middle_value:]
            
            oprs = sorted(zip(event.oprs,event.opr_teams), reverse=True) # sort by OPR
            oprs = oprs[:14] # get the top 15 OPRs
        
            template_values = {
                "event": event,
                "matches": matches,
                "teams_a": teams_a,
                "teams_b": teams_b,
                "num_teams": num_teams,
                "oprs": oprs,
            }
                
            path = os.path.join(os.path.dirname(__file__), '../templates/event_details.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 300)
        
        self.response.out.write(html)

class EventRss(webapp.RequestHandler):
    """
    Generates a RSS feed for the matches in a event
    Created by: @brandondean, github.com/brandondean
    """
    def get(self, event_key):
        memcache_key = "event_rss_%s" % event_key
        html = memcache.get(memcache_key)
        
        if html is None:
            event = Event.get_by_key_name(event_key)
            matches = MatchHelper.organizeMatches(event.match_set)
            
            rss_items = []
            # Loop through and generate RSS items for each match
            for match in matches['f'] + matches['sf'] + matches['qf'] + matches['ef'] + matches['qm']:
                match.unpack_json()
                new_item = PyRSS2Gen.RSSItem(
                    title = str(match.verbose_name()),
                    link = 'http://www.thebluealliance.com/match/' + match.get_key_name() + '',
                    
                    # List the red and blue alliance teams and their score
                    # TODO: Make this generic in case there's ever not just red/blue -gregmarra 12 Mar 2011
                    # TODO: Make this output format something either very machine or very human readable.
                    # Probably opt for human, since machines should be using the API. -gregmarra 12 Mar 2011
                    description = "Red Alliance: " + ' '.join(match.alliances["red"]["teams"]) + " "
                                  + "Score: " + str(match.alliances["red"]["score"]) + " "
                                  + "Blue Alliance: " + ' '.join(match.alliances["blue"]["teams"]) + " "
                                  + "Score: " + str(match.alliances["blue"]["score"])
         
                )
                rss_items.append(new_item)
            
            # Create final rss document
            rss = PyRSS2Gen.RSS2(
                title = event.name + "-- " + str(event.year),
                link = 'http://www.thebluealliance.com/event/' + str(event.get_key_name()) + '',
                description = "RSS feed for the " + event.name + " provided by The Blue Alliance." ,
                lastBuildDate = datetime.datetime.now(),
                items = rss_items
            )
            html = rss.to_xml()
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 300)
        
        self.response.out.write(html)
