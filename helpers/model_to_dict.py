from datetime import datetime
import json
import logging

from  models.award import Award
from  models.event import Event
from  models.team import Team

class ModelToDict(object):

    @classmethod
    def teamConverter(self, team):
        """
        return top level team dictionary
        """
        team_dict = dict()
        team_dict["key"] = team.key_name
        team_dict["team_number"] = team.team_number
        team_dict["name"] = team.name
        team_dict["nickname"] = team.nickname
        team_dict["website"] = team.website
        team_dict["location"] = team.location

        try:
            team_dict["location"] = team.location
            team_dict["locality"] = team.locality
            team_dict["region"] = team.region
            team_dict["country_name"] = team.country_name
        except Exception, e:
            logging.warning("Failed to include Address for api_team_info_%s: %s" % (team_key, e))

        return team_dict

    @classmethod
    def eventConverter(self, event):
        """
        return top level event dictionary
        """
        event_dict = dict()
        event_dict["key"] = event.key_name
        event_dict["name"] = event.name
        event_dict["short_name"] = event.short_name
        event_dict["event_code"] = event.event_short
        event_dict["event_type"] = event.event_type_enum
        event_dict["year"] = event.year
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

        return event_dict

    @classmethod
    def matchConverter(self, match):
        """
        return top level match dictionary
        """
        match_dict = dict()
        match_dict["key"] = match.key_name
        match_dict["event_key"] = match.event.id()
        match_dict["alliances"] = json.loads(match.alliances_json)
        match_dict["team_keys"] = match.team_key_names
        match_dict["game"] = match.game
        match_dict["comp_level"] = match.comp_level
        match_dict["match_number"] = match.match_number
        match_dict["set_number"] = match.set_number

        return match_dict

    @classmethod
    def awardConverter(self, award):
        """
        return top level award dictionary
        """
        award_dict = dict()
        award_dict["name_str"] = award.name_str
        award_dict["award_type"] = award.award_type_enum
        award_dict["year"] = award.year
        award_dict["event_key"] = award.event.id()
        award_dict["recipient_list"] = award.recipient_list

        return award_dict
