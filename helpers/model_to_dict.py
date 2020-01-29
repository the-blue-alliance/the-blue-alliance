import logging
import time


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
        team_dict["rookie_year"] = team.rookie_year
        team_dict["motto"] = None

        try:
            team_dict["location"] = team.location
            team_dict["locality"] = team.city
            team_dict["region"] = team.state_prov
            team_dict["country_name"] = team.country
            team_dict["school_name"] = team.school_name
        except Exception, e:
            logging.warning("Failed to include Address for api_team_info_%s: %s" % (team.key.id(), e))

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
        event_dict["event_type_string"] = event.event_type_str
        event_dict["event_type"] = event.event_type_enum
        event_dict["event_district_string"] = event.event_district_str
        event_dict["event_district"] = event.event_district_enum
        event_dict["year"] = event.year
        event_dict["location"] = event.location
        event_dict["venue_address"] = event.venue_address_safe
        event_dict["official"] = event.official
        event_dict["facebook_eid"] = event.facebook_eid
        event_dict["website"] = event.website
        event_dict["timezone"] = event.timezone_id
        event_dict["week"] = event.week

        if event.alliance_selections:
            event_dict["alliances"] = event.alliance_selections
        else:
            event_dict["alliances"] = []
        if event.start_date:
            event_dict["start_date"] = event.start_date.date().isoformat()
        else:
            event_dict["start_date"] = None
        if event.end_date:
            event_dict["end_date"] = event.end_date.date().isoformat()
        else:
            event_dict["end_date"] = None

        if event.webcast:
            event_dict["webcast"] = event.webcast
        else:
            event_dict["webcast"] = []

        return event_dict

    @classmethod
    def favoriteConverter(self, favorite):
        return {
            'model_type': favorite.model_type,
            'model_key': favorite.model_key
        }

    @classmethod
    def matchConverter(self, match):
        """
        return top level match dictionary
        """
        match_dict = dict()
        match_dict["key"] = match.key_name
        match_dict["event_key"] = match.event.id()
        match_dict["alliances"] = match.alliances
        match_dict["score_breakdown"] = match.score_breakdown
        match_dict["comp_level"] = match.comp_level
        match_dict["match_number"] = match.match_number
        match_dict["set_number"] = match.set_number
        match_dict["videos"] = match.videos
        match_dict["time_string"] = match.time_string
        if match.time is not None:
            match_dict["time"] = int(time.mktime(match.time.timetuple()))
        else:
            match_dict["time"] = None

        return match_dict

    @classmethod
    def awardConverter(self, award):
        """
        return top level award dictionary
        """
        award_dict = dict()
        award_dict["name"] = award.name_str
        award_dict["award_type"] = award.award_type_enum
        award_dict["year"] = award.year
        award_dict["event_key"] = award.event.id()
        award_dict["recipient_list"] = award.recipient_list

        return award_dict

    @classmethod
    def mediaConverter(self, media):
        """
        return top level media dictionary
        """
        media_dict = dict()
        media_dict["type"] = media.slug_name
        media_dict["foreign_key"] = media.foreign_key
        if media.details is not None:
            media_dict["details"] = media.details
        else:
            media_dict["details"] = {}
        media_dict["preferred"] = True if media.preferred_references != [] else False

        return media_dict

    @classmethod
    def robotConverter(self, robot):
        """
        return top level robot dict
        """
        robot_dict = dict()
        robot_dict["key"] = robot.key_name
        robot_dict["team_key"] = robot.team.id()
        robot_dict["year"] = robot.year
        robot_dict["name"] = robot.robot_name
        return robot_dict
