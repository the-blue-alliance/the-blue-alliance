import json
import logging
import os
import webapp2

from datetime import datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

import tba_config
from helpers.api_helper import ApiHelper
from helpers.api.api_model_to_dict import ApiModelToDict

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

#Note: generally caching for the API happens in ApiHelper

class MainApiHandler(webapp2.RequestHandler):

    def __init__(self, request, response):
        # Need to initialize a webapp2 instance
        self.initialize(request, response)
        logging.info(request)

class ApiTeamsShow(MainApiHandler):
    """
    Information about teams.
    """
    def get(self):
        teams = list()
        team_keys = self.request.get('teams').split(',')

        for team_key in team_keys:
            memcache_key = "api_%s" % team_key
            team_dict = memcache.get(team_key)

            if team_dict is None:
                team = Team.get_by_id(team_key)
                if team is not None:
                    team_dict = ApiModelToDict.teamConverter(team)

                    event_teams = EventTeam.query(EventTeam.team == team.key,\
                                                  EventTeam.year == datetime.now().year)\
                                                  .fetch(1000, projection=[EventTeam.event])
                    event_ids = [event_team.event for event_team in event_teams]
                    events = ndb.get_multi(event_ids)

                    game = Match.FRC_GAMES_BY_YEAR[2010]
                    matches = Match.query(Match.team_key_names == team.key_name,\
                                          Match.game == game).fetch(1000)

                    team_dict["events"] = list()
                    for event in events:
                        event_dict = ApiModelToDict.eventConverter(event)

                        event_dict["matches"] = [ApiModelToDict.matchConverter(match) for match in matches if match.event is event.key]

                        team_dict["events"].append(event_dict)


                    #TODO: Reduce caching time before 2013 season. 2592000 is one month -gregmarra 
                    if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, team_dict, 2592000)
                    teams.append(team_dict)
                else:
                    raise IndexError


        self.response.out.write(json.dumps(teams))


class ApiTeamDetails(MainApiHandler):
    """
    Information about a Team in a particular year, including full Event and Match objects
    """
    def get(self):

        team_key = self.request.get('team')
        year = self.request.get('year')

        response_json = dict()
        try:
            response_json = ApiHelper.getTeamInfo(team_key)
            if self.request.get('events'):
                reponse_json = ApiHelper.addTeamEvents(response_json, year)
            
            #TODO: matches
            
            self.response.out.write(json.dumps(response_json))

        except IndexError:
            response_json = { "Property Error": "No team found for the key given" }
            self.response.out.write(json.dumps(response_json))

class ApiEventsShow(MainApiHandler):
    """
    Information about events.
    Deprecation notice. Please use ApiEventList, or ApiEventDetails.
    """
    def get(self):
        response = { "API Method Removed": "ApiEventsShow is no longer available. Please use ApiEvenDetails, and ApiEventList instead." }
        self.response.set_status(410)
        self.response.out.write(json.dumps(response))

class ApiEventList(MainApiHandler):
    """
    Returns a list of events for a year with top level information
    """

    def get(self):
        if self.request.get("year") is '':
            year = datetime.now().year
        else:
            year = int(self.request.get("year"))

        memcache_key = "api_event_list_%s" % year
        event_list = memcache.get(memcache_key)

        if event_list is None:
            event_list = []
            events = Event.query(Event.year == year).fetch(500)
            for event in events:
                event_dict = dict()
                event_dict["key"] = event.key_name
                event_dict["name"] = event.name
                event_dict["short_name"] = event.short_name
                event_dict["official"] = event.official
                
                if event.start_date:
                    event_dict["start_date"] = event.start_date.isoformat()
                else:
                    event_dict["start_date"] = None
                if event.end_date:
                    event_dict["end_date"] = event.end_date.isoformat()
                else:
                    event_dict["end_date"] = None

                event_list.append(event_dict)

            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, event_list, (30 * ((60 * 60) * 24)))

        self.response.headers.add_header("content-type", "application/json")
        self.response.out.write(json.dumps(event_list))

class ApiEventDetails(MainApiHandler):
    """
    Return a specifc event with details.
    """

    def get(self):
        event_key = str(self.request.get("event"))
        if event_key is "" or event_key is None:
            error_message = {"Parameter Error": "'event' is a required parameter."}
            self.response.out.write(json.dumps(error_message))
            return False

        

        event_dict = ApiHelper.getEventInfo(event_key)

        self.response.out.write(json.dumps(event_dict))

class ApiMatchDetails(MainApiHandler):
    """
    Returns a specifc
    """
    def get(self):
        if self.request.get('match') is not '':
            match_key = self.request.get('match')

        if self.request.get('matches') is not '':
            match_keys = self.request.get('matches').split(',')

        if 'match_keys' in locals():
            match_json = list()
            for match in match_keys:
                match_json.append(ApiHelper.getMatchDetails(match))
        else:
            match_json = ApiHelper.getMatchDetails(match_key)

        self.response.headers.add_header("content-type", "application/json")
        self.response.out.write(json.dumps(match_json))

class CsvTeamsAll(MainApiHandler):
    """
    Outputs a CSV of all team information in the database, designed for other apps to bulk-import data.
    """
    def get(self):
        memcache_key = "csv_teams_all"
        output = memcache.get(memcache_key)
    
        if output is None:
            teams = Team.query().order(Team.team_number).fetch(10000)        

            template_values = {
                "teams": teams
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/api/csv_teams_all.csv')
            output = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, output, 86400)
        
        self.response.out.write(output)
