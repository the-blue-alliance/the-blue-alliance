import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.team_helper import TeamHelper
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class EventList(BaseHandler):
    """
    List all Events.
    """
    def get(self, year=None):
        
        show_upcoming = False
        valid_years = [2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002]

        if year:
            if not year.isdigit():
                return self.redirect("/error/404")
            year = int(year)
            if year not in valid_years:
                return self.redirect("/error/404")
            explicit_year = True
            if year == datetime.datetime.now().year:
                show_upcoming = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False
            show_upcoming = True
        
        memcache_key = "event_list_%s" % year
        html = memcache.get(memcache_key)
        
        if html is None:
            events = Event.all().filter("year =", int(year)).order('start_date').fetch(1000)
        
            template_values = {
                "show_upcoming": show_upcoming,
                "events": events,
                "explicit_year": explicit_year,
                "selected_year": year,
                "valid_years": valid_years,
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/event_list.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400) 
        
        self.response.out.write(html)
        
class EventDetail(BaseHandler):
    """
    Show an Event.
    event_code like "2010ct"
    """
    def get(self, event_key):
        
        if not event_key:
            return self.redirect("/events")
        
        memcache_key = "event_detail_%s" % event_key
        html = memcache.get(memcache_key)
        
        if html is None:
            event = Event.get_by_key_name(event_key)
            
            if not event:
                return self.redirect("/error/404")
            
            matches = MatchHelper.organizeMatches(event.match_set)
            awards = AwardHelper.organizeAwards(event.award_set)
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
                "awards": awards,
                "teams_a": teams_a,
                "teams_b": teams_b,
                "num_teams": num_teams,
                "oprs": oprs,
                "bracket_table": bracket_table,
            }
                
            path = os.path.join(os.path.dirname(__file__), '../templates/event_details.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
        
        self.response.out.write(html)

class EventRss(BaseHandler):
    """
    Generates a RSS feed for the matches in a event
    """
    def get(self, event_key):
        memcache_key = "event_rss_%s" % event_key
        xml = memcache.get(memcache_key)
        
        if xml is None:
            event = Event.get_by_key_name(event_key)
            matches = MatchHelper.organizeMatches(event.match_set)
        
            template_values = {
                    "event": event,
                    "matches": matches,
                    "datetime": datetime.datetime.now()
            }

            path = os.path.join(os.path.dirname(__file__),
                '../templates/event_rss.xml')
            xml = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, 
                                                            xml,
                                                            86500)

        self.response.headers.add_header('content-type', 'application/xml', charset='utf-8')        
        self.response.out.write(xml)
