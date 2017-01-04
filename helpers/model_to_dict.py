import logging
import time

from consts.district_type import DistrictType
from consts.media_type import MediaType


class ModelToDict(object):
    @classmethod
    def constructLocation_v3(cls, model):
        """
        Works for teams and events
        """
        has_nl = model.nl and model.nl.city and model.nl.state_prov and model.nl.country
        return {
            'city': model.nl.city if has_nl else model.city,
            'state_prov': model.nl.state_prov if has_nl else model.state_prov,
            'country': model.nl.country if has_nl else model.country,
            'postal_code': model.nl.postal_code if has_nl else model.postalcode,
            'lat': model.nl.lat_lng.lat if has_nl else None,
            'lng': model.nl.lat_lng.lon if has_nl else None,
            'location_name': model.nl.name if has_nl else None,
            'address': model.nl.formatted_address if has_nl else None,
            'gmaps_place_id': model.nl.place_id if has_nl else None,
            'gmaps_url': model.nl.place_details.get('url') if has_nl else None,
        }

    @classmethod
    def convertTeams(cls, teams, dict_version):
        TEAM_CONVERTERS = {
            '3': cls.teamsConverter_v3,
        }
        return TEAM_CONVERTERS[dict_version](teams)

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
        team_dict["motto"] = team.motto

        try:
            team_dict["location"] = team.location
            team_dict["locality"] = team.city
            team_dict["region"] = team.state_prov
            team_dict["country_name"] = team.country
        except Exception, e:
            logging.warning("Failed to include Address for api_team_info_%s: %s" % (team.key.id(), e))

        return team_dict

    @classmethod
    def teamsConverter_v3(cls, teams):
        return map(cls.teamConverter_v3, teams)

    @classmethod
    def teamConverter_v3(cls, team):
        has_nl = team.nl and team.nl.city and team.nl.state_prov and team.nl.country
        team_dict = {
            'key': team.key.id(),
            'team_number': team.team_number,
            'nickname': team.nickname,
            'name': team.name,
            'website': team.website,
            'rookie_year': team.rookie_year,
            'motto': team.motto,
            'home_championship': team.championship_location,
        }
        team_dict.update(cls.constructLocation_v3(team))
        return team_dict

    @classmethod
    def convertEvents(cls, events, dict_version):
        EVENT_CONVERTERS = {
            '3': cls.eventsConverter_v3,
        }
        return EVENT_CONVERTERS[dict_version](events)

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
    def eventsConverter_v3(cls, events):
        events = map(cls.eventConverter_v3, events)
        return events

    @classmethod
    def eventConverter_v3(cls, event):
        event_dict = {
            'key': event.key.id(),
            'name': event.name,
            'short_name': event.short_name,
            'event_code': event.event_short,
            'event_type': event.event_type_enum,
            'event_type_string': event.event_type_str,
            'district_type': event.event_district_enum,
            'district_type_string': event.event_district_str,
            'first_event_id': event.first_eid,
            'year': event.year,
            'timezone': event.timezone_id,
            'week': event.week,
            'website': event.website,
        }
        event_dict.update(cls.constructLocation_v3(event))

        if event.start_date:
            event_dict['start_date'] = event.start_date.date().isoformat()
        else:
            event_dict['start_date'] = None
        if event.end_date:
            event_dict['end_date'] = event.end_date.date().isoformat()
        else:
            event_dict['end_date'] = None

        if event.webcast:
            event_dict['webcasts'] = event.webcast
        else:
            event_dict['webcasts'] = []

        return event_dict

    @classmethod
    def favoriteConverter(self, favorite):
        return {
            'model_type': favorite.model_type,
            'model_key': favorite.model_key
        }

    @classmethod
    def convertMatches(cls, matches, dict_version):
        MATCH_CONVERTERS = {
            '3': cls.matchesConverter_v3,
        }
        return MATCH_CONVERTERS[dict_version](matches)

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
    def matchesConverter_v3(cls, matches):
        return map(cls.matchConverter_v3, matches)

    @classmethod
    def matchConverter_v3(cls, match):
        match_dict = {
            'key': match.key.id(),
            'event_key': match.event.id(),
            'comp_level': match.comp_level,
            'set_number': match.set_number,
            'match_number': match.match_number,
            'alliances': match.alliances,
            'winning_alliance': match.winning_alliance,
            'score_breakdown': match.score_breakdown,
            'videos': match.videos,
        }
        if match.time is not None:
            match_dict['time'] = int(time.mktime(match.time.timetuple()))
        else:
            match_dict['time'] = None
        if match.actual_time is not None:
            match_dict['actual_time'] = int(time.mktime(match.actual_time.timetuple()))
        else:
            match_dict['actual_time'] = None

        return match_dict

    @classmethod
    def convertAwards(cls, awards, dict_version):
        AWARD_CONVERTERS = {
            '3': cls.awardsConverter_v3,
        }
        return AWARD_CONVERTERS[dict_version](awards)

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
    def awardsConverter_v3(cls, awards):
        awards = map(cls.awardConverter_v3, awards)
        return awards

    @classmethod
    def awardConverter_v3(cls, award):
        recipient_list_fixed = []
        for recipient in award.recipient_list:
            recipient_list_fixed.append({
                'awardee': recipient['awardee'],
                'team_key': 'frc{}'.format(recipient['team_number']),
            })
        return {
            'name': award.name_str,
            'award_type': award.award_type_enum,
            'year': award.year,
            'event_key': award.event.id(),
            'recipient_list': recipient_list_fixed,
        }

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

    @classmethod
    def convertRobots(cls, robots, dict_version):
        ROBOT_CONVERTERS = {
            '3': cls.robotsConverter_v3,
        }
        return ROBOT_CONVERTERS[dict_version](robots)

    @classmethod
    def robotsConverter_v3(cls, robots):
        robots_dict = {}
        for robot in robots:
            robots_dict[robot.year] = cls.robotConverter_v3(robot)
        return robots_dict

    @classmethod
    def robotConverter_v3(cls, robot):
        return {
            'key': robot.key_name,
            'team_key': robot.team.id(),
            'year': robot.year,
            'robot_name': robot.robot_name,
        }
