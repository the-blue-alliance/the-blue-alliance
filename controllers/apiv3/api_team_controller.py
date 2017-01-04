import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import team_properties, event_properties, match_properties
from database.award_query import TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery
from database.event_query import TeamEventsQuery, TeamYearEventsQuery
from database.match_query import TeamEventMatchesQuery, TeamYearMatchesQuery
from database.media_query import TeamYearMediaQuery, TeamSocialMediaQuery
from database.team_query import TeamQuery, TeamListQuery, TeamListYearQuery, TeamParticipationQuery, TeamDistrictsQuery
from database.robot_query import TeamRobotsQuery
from models.team import Team


class ApiTeamListController(ApiBaseController):
    """
    Returns a JSON list of teams, paginated by team number in sets of 500
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24
    PAGE_SIZE = 500

    def _track_call(self, page_num, year=None, model_type=None):
        action = 'team/list'
        if year:
            action += '/{}'.format(year)
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, page_num)

    def _render(self, page_num, year=None, model_type=None):
        if year is None:
            team_list = TeamListQuery(int(page_num)).fetch(dict_version='3')
        else:
            team_list = TeamListYearQuery(int(year), int(page_num)).fetch(dict_version='3')
        if model_type is not None:
            team_list = [{key: team[key] for key in team_properties[model_type]} for team in team_list]
        return json.dumps(team_list, ensure_ascii=True)


class ApiTeamController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key, model_type=None):
        action = 'team'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, team_key)

    def _render(self, team_key, model_type=None):
        team = TeamQuery(team_key).fetch(dict_version='3')
        if model_type is not None:
            team = {key: team[key] for key in team_properties[model_type]}

        return json.dumps(team, ensure_ascii=True)


class ApiTeamYearsParticipatedController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key):
        self._track_call_defer('team/years_participated', team_key)

    def _render(self, team_key):
        years_participated = sorted(TeamParticipationQuery(team_key).fetch())

        return json.dumps(years_participated, ensure_ascii=True)


class ApiTeamHistoryDistrictsController(ApiBaseController):
    """
    Returns a JSON list of all DistrictTeam models associated with a Team
    """
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key):
        self._track_call_defer('team/history/districts', team_key)

    def _render(self, team_key):
        team_districts = TeamDistrictsQuery(team_key).fetch()

        return json.dumps(team_districts, ensure_ascii=True)


class ApiTeamHistoryRobotsController(ApiBaseController):
    """
    Returns a JSON list of all robot models associated with a Team
    """
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key):
        self._track_call_defer('team/history/robots', team_key)

    def _render(self, team_key):
        robots = TeamRobotsQuery(team_key).fetch(dict_version='3')

        return json.dumps(robots, ensure_ascii=True)


class ApiTeamEventsController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key, year=None, model_type=None):
        api_label = team_key
        if year:
            api_label += '/{}'.format(year)
        action = 'team/events'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, api_label)

    def _render(self, team_key, year=None, model_type=None):
        if year:
            events = TeamYearEventsQuery(team_key, int(year)).fetch(dict_version='3')
        else:
            events = TeamEventsQuery(team_key).fetch(dict_version='3')
        if model_type is not None:
            events = [{key: event[key] for key in event_properties[model_type]} for event in events]
        return json.dumps(events, ensure_ascii=True)


class ApiTeamEventMatchesController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, event_key, model_type=None):
        action = 'team/event/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key, model_type=None):
        matches = TeamEventMatchesQuery(team_key, event_key).fetch(dict_version='3')
        if model_type is not None:
            matches = [{key: match[key] for key in match_properties[model_type]} for match in matches]

        return json.dumps(matches, ensure_ascii=True)


class ApiTeamYearMatchesController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, year, model_type=None):
        action = 'team/year/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(team_key, year))

    def _render(self, team_key, year, model_type=None):
        matches = TeamYearMatchesQuery(team_key, int(year)).fetch(dict_version='3')
        if model_type is not None:
            matches = [{key: match[key] for key in match_properties[model_type]} for match in matches]

        return json.dumps(matches, ensure_ascii=True)


class ApiTeamEventAwardsController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60

    def _track_call(self, team_key, event_key):
        self._track_call_defer('team/event/awards', '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key):
        awards = TeamEventAwardsQuery(team_key, event_key).fetch(dict_version='3')

        return json.dumps(awards, ensure_ascii=True)


class ApiTeamYearAwardsController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60

    def _track_call(self, team_key, year):
        self._track_call_defer('team/year/awards', '{}/{}'.format(team_key, year))

    def _render(self, team_key, year):
        awards = TeamYearAwardsQuery(team_key, int(year)).fetch(dict_version='3')

        return json.dumps(awards, ensure_ascii=True)


class ApiTeamHistoryAwardsController(ApiBaseController):
    """
    Returns a JSON list of award models won by a team
    """
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60

    def _track_call(self, team_key):
        self._track_call_defer('team/history/awards', team_key)

    def _render(self, team_key):
        awards = TeamAwardsQuery(team_key).fetch(dict_version='3')

        return json.dumps(awards, ensure_ascii=True)


class ApiTeamYearMediaController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key, year):
        api_label = team_key
        api_label += '/{}'.format(year)
        self._track_call_defer('team/media', api_label)

    def _render(self, team_key, year):
        medias = TeamYearMediaQuery(team_key, int(year)).fetch(dict_version='3')

        return json.dumps(medias, ensure_ascii=True)


class ApiTeamSocialMediaController(ApiBaseController):
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, team_key):
        self._track_call_defer('team/social_media', team_key)

    def _render(self, team_key):
        social_medias = TeamSocialMediaQuery(team_key).fetch(dict_version='3')

        return json.dumps(social_medias, ensure_ascii=True)
