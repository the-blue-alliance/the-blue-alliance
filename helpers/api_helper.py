import logging

from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import db

from models import Team, Match
from helpers.match_helper import MatchHelper

class ApiHelper(object):
    """Helper for api_controller."""
    @classmethod
    def getTeamInfo(self, team_key):
        """
        Return a Team object with basic information.
        """
        memcache_key = "api_team_info_%s" % team_key
        team_dict = memcache.get(memcache_key)
        if team_dict is None:
            team = Team.get_by_key_name(team_key)
            if Team is not None:
                team_dict = dict()
                team_dict["key"] = team.key().name()
                team_dict["team_number"] = team.team_number
                team_dict["name"] = team.name
                team_dict["nickname"] = team.nickname
                team_dict["location"] = team.address
                team_dict["website"] = team.website
                team_dict["events"] = [a.event.key().name() for a in team.events]
                
                memcache.set(memcache_key, team_dict, 3600)
            else:
                return None
        return team_dict

    @classmethod
    def addTeamDetails(self, team_dict, year):
        """
        Consume a Team dict, and return it with a year's Events filtered and Matches added
        """
        
        # TODO Matches should live under Events - gregmarra 1 feb 2011
        # TODO Filter Events by year - gregmarra 1 feb 2011
        
        memcache_key = "api_team_details_%s_%s" % (team_dict["key"], year)
        matches_list = memcache.get(memcache_key)
        if matches_list is None:
            matches = list()
            team = Team.get_by_key_name(team_dict["key"])
            for e in [a.event for a in team.events]:
                match_list = e.match_set.filter("team_key_names =", team.key().name()).fetch(500)
                matches.extend(match_list)
            matches_list = list()
            for match in matches:
                match_dict = dict()
                match_dict["key"] = match.key().name()
                match_dict["event"] = match.event.key().name()
                match_dict["comp_level"] = match.comp_level
                match_dict["set_number"] = match.set_number
                match_dict["match_number"] = match.match_number
                match_dict["team_keys"] = match.team_key_names
                match_dict["alliances"] = simplejson.loads(match.alliances_json)
                matches_list.append(match_dict)
            
            memcache.set(memcache_key, matches_list, 600)
        
        team_dict["matches"] = matches_list
        return team_dict