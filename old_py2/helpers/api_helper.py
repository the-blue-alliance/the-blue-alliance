import json
import logging
from datetime import datetime

from google.appengine.api import memcache

import tba_config
from helpers.event_helper import EventHelper

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team


class ApiHelper(object):
    """Helper for api_controller."""
    @classmethod
    def getTeamInfo(cls, team_key):
        """
        Return a Team dict with basic information.
        """
        memcache_key = "api_team_info_%s" % team_key
        team_dict = memcache.get(memcache_key)
        if team_dict is None:
            team = Team.get_by_id(team_key)
            if team is not None:
                team_dict = dict()
                team_dict["key"] = team.key_name
                team_dict["team_number"] = team.team_number
                team_dict["name"] = team.name
                team_dict["nickname"] = team.nickname
                team_dict["website"] = team.website
                team_dict["location"] = team.location

                event_teams = EventTeam.query(EventTeam.team == team.key,
                                              EventTeam.year == datetime.now().year)\
                                              .fetch(1000, projection=[EventTeam.event])
                team_dict["events"] = [event_team.event.id() for event_team in event_teams]

                try:
                    team_dict["location"] = team.location
                    team_dict["locality"] = team.city
                    team_dict["region"] = team.state_prov
                    team_dict["country_name"] = team.country
                except Exception, e:
                    logging.warning("Failed to include Address for api_team_info_%s: %s" % (team_key, e))

                # TODO: Reduce caching time before 2013 season. 2592000 is one month -gregmarra
                if tba_config.CONFIG["memcache"]:
                    memcache.set(memcache_key, team_dict, 2592000)
            else:
                raise IndexError

        return team_dict

    @classmethod
    def getEventInfo(cls, event_key):
        """
        Return an Event dict with basic information
        """

        memcache_key = "api_event_info_%s" % event_key
        event_dict = memcache.get(memcache_key)
        if event_dict is None:
            event = Event.get_by_id(event_key)
            if event is not None:
                event_dict = dict()
                event_dict["key"] = event.key_name
                event_dict["year"] = event.year
                event_dict["event_code"] = event.event_short
                event_dict["name"] = event.name
                event_dict["short_name"] = event.short_name
                event_dict["location"] = event.location
                event_dict["official"] = event.official
                event_dict["facebook_eid"] = event.facebook_eid

                if event.start_date:
                    event_dict["start_date"] = event.start_date.isoformat()
                else:
                    event_dict["start_date"] = None
                if event.end_date:
                    event_dict["end_date"] = event.end_date.isoformat()
                else:
                    event_dict["end_date"] = None

                event.prepTeamsMatches()
                event_dict["teams"] = [team.key_name for team in event.teams]
                event_dict["matches"] = [match.key_name for match in event.matches]

                if tba_config.CONFIG["memcache"]:
                    memcache.set(memcache_key, event_dict, 60 * 60)
        return event_dict

    @classmethod
    def addTeamEvents(cls, team_dict, year):
        """
        Consume a Team dict, and return it with a year's Events.
        """
        memcache_key = "api_team_events_%s_%s" % (team_dict["key"], year)
        event_list = memcache.get(memcache_key)

        if event_list is None:
            team = Team.get_by_id(team_dict["key"])
            events = [a.event.get() for a in EventTeam.query(EventTeam.team == team.key, EventTeam.year == int(year)).fetch(1000)]
            events = sorted(events, key=lambda event: event.start_date)
            event_list = [cls.getEventInfo(e.key_name) for e in events]
            for event_dict, event in zip(event_list, events):
                event_dict["team_wlt"] = EventHelper.getTeamWLT(team_dict["key"], event)

            # TODO: Reduce caching time before 2013 season. 2592000 is one month -gregmarra
            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, event_list, 2592000)

        team_dict["events"] = event_list
        return team_dict

    @classmethod
    def addTeamDetails(cls, team_dict, year):
        """
        Consume a Team dict, and return it with a year's Events filtered and Matches added
        """

        # TODO Matches should live under Events - gregmarra 1 feb 2011
        # TODO Filter Events by year - gregmarra 1 feb 2011

        memcache_key = "api_team_details_%s_%s" % (team_dict["key"], year)
        matches_list = memcache.get(memcache_key)
        if matches_list is None:
            matches = list()
            team = Team.get_by_id(team_dict["key"])
            for e in [a.event.get() for a in EventTeam.query(EventTeam.team == team.key).fetch(1000) if a.year == year]:
                match_list = Match.query(Match.event == event.key, Match.team_key_names == team.key_name).fetch(500)
                matches.extend(match_list)
            matches_list = list()
            for match in matches:
                match_dict = dict()
                match_dict["key"] = match.key_name
                match_dict["event"] = match.event
                match_dict["comp_level"] = match.comp_level
                match_dict["set_number"] = match.set_number
                match_dict["match_number"] = match.match_number
                match_dict["team_keys"] = match.team_key_names
                match_dict["alliances"] = json.loads(match.alliances_json)
                matches_list.append(match_dict)

            # TODO: Reduce caching time before 2013 season. 2592000 is one month -gregmarra
            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, matches_list, 2592000)

        team_dict["matches"] = matches_list
        return team_dict

    @classmethod
    def getMatchDetails(cls, match_key):
        """
        Returns match details
        """
        memcache_key = "api_match_details_%s" % match_key
        match_dict = memcache.get(memcache_key)

        if match_dict is None:
            match = Match.get_by_id(match_key)
            if match is None:
                return None

            match_dict = {}
            match_dict["key"] = match.key_name
            match_dict["event"] = match.event.id()
            match_dict["competition_level"] = match.name
            match_dict["set_number"] = match.set_number
            match_dict["match_number"] = match.match_number
            match_dict["team_keys"] = match.team_key_names
            match_dict["alliances"] = json.loads(match.alliances_json)
            match_dict["videos"] = match.videos
            match_dict["time_string"] = match.time_string
            if match.time is not None:
                match_dict["time"] =  match.time.strftime("%s")
            else:
                match_dict["time"] = None

            if tba_config.CONFIG["memcache"]:
                memcache.set(memcache_key, match_dict, (2 * (60 * 60)))

        return match_dict
