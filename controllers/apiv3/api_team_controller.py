import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import team_properties, event_properties, match_properties
from database.award_query import TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery
from database.event_query import TeamEventsQuery, TeamYearEventsQuery
from database.match_query import TeamEventMatchesQuery, TeamYearMatchesQuery
from database.media_query import TeamYearMediaQuery
from database.team_query import TeamListQuery, TeamListYearQuery, TeamParticipationQuery, TeamDistrictsQuery
from database.robot_query import TeamRobotsQuery
from helpers.model_to_dict import ModelToDict
from models.team import Team


class ApiTeamControllerBase(ApiBaseController):
    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _set_team(self, team_key):
        self.team = Team.get_by_id(team_key)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % team_key})
            self.abort(404)


class ApiTeamListController(ApiTeamControllerBase):
    """
    Returns a JSON list of teams, paginated by team number in sets of 500
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    CACHE_KEY_FORMAT = "apiv3_team_list_controller_{}_{}_{}"  # (page_num, year, model_type)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24
    PAGE_SIZE = 500

    def __init__(self, *args, **kw):
        super(ApiTeamListController, self).__init__(*args, **kw)
        self.page_num = self.request.route_kwargs['page_num']
        self.year = self.request.route_kwargs.get('year')
        self.model_type = self.request.route_kwargs.get('model_type')
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.page_num, self.year, self.model_type)

    @property
    def _validators(self):
        return []

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


class ApiTeamController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_controller_{}_{}"  # (team_key, model_type)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.model_type = self.request.route_kwargs.get('model_type')
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.model_type)

    def _track_call(self, team_key, model_type=None):
        action = 'team'
        if self.model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, team_key)

    def _render(self, team_key, model_type=None):
        self._set_team(team_key)

        team = ModelToDict.teamConverter_v3(self.team)
        if model_type is not None:
            team = {key: team[key] for key in team_properties[model_type]}

        return json.dumps(team, ensure_ascii=True)


class ApiTeamYearsParticipatedController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_years_participated_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamYearsParticipatedController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/years_participated', team_key)

    def _render(self, team_key):
        years_participated = sorted(TeamParticipationQuery(self.team_key).fetch())

        return json.dumps(years_participated, ensure_ascii=True)


class ApiTeamHistoryDistrictsController(ApiTeamControllerBase):
    """
    Returns a JSON list of all DistrictTeam models associated with a Team
    """
    CACHE_KEY_FORMAT = "apiv3_team_history_districts_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryDistrictsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/districts', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        team_districts = TeamDistrictsQuery(self.team_key).fetch()

        return json.dumps(team_districts, ensure_ascii=True)


class ApiTeamHistoryRobotsController(ApiTeamControllerBase):
    """
    Returns a JSON list of all robot models associated with a Team
    """
    CACHE_KEY_FORMAT = "apiv3_team_history_robots_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryRobotsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/robots', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        robots = TeamRobotsQuery(self.team_key).fetch(dict_version='3')

        return json.dumps(robots, ensure_ascii=True)


class ApiTeamEventsController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_events_controller_{}_{}_{}"  # (team_key, year, model_type)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamEventsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = self.request.route_kwargs.get("year")
        self.model_type = self.request.route_kwargs.get('model_type')
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year, self.model_type)

    def _track_call(self, team_key, year=None, model_type=None):
        api_label = team_key
        if year:
            api_label += '/{}'.format(year)
        action = 'team/events'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, api_label)

    def _render(self, team_key, year=None, model_type=None):
        self._set_team(team_key)

        if year:
            events = TeamYearEventsQuery(self.team_key, int(year)).fetch(dict_version='3')
        else:
            events = TeamEventsQuery(self.team_key).fetch(dict_version='3')
        if model_type is not None:
            events = [{key: event[key] for key in event_properties[model_type]} for event in events]
        return json.dumps(events, ensure_ascii=True)


class ApiTeamEventMatchesController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_event_matches_controller_{}_{}_{}"  # (team_key, event_key, model_type)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiTeamEventMatchesController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.event_key = self.request.route_kwargs["event_key"]
        self.model_type = self.request.route_kwargs.get('model_type')
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.event_key, self.model_type)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key), ("event_id_validator", self.event_key)]

    def _track_call(self, team_key, event_key, model_type=None):
        action = 'team/event/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key, model_type=None):
        matches = TeamEventMatchesQuery(self.team_key, self.event_key).fetch(dict_version='3')
        if model_type is not None:
            matches = [{key: match[key] for key in match_properties[model_type]} for match in matches]

        return json.dumps(matches, ensure_ascii=True)


class ApiTeamYearMatchesController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_year_matches_controller_{}_{}_{}"  # (team_key, year, model_type)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiTeamYearMatchesController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = self.request.route_kwargs["year"]
        self.model_type = self.request.route_kwargs.get('model_type')
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year, self.model_type)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _track_call(self, team_key, year, model_type=None):
        action = 'team/year/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(team_key, year))

    def _render(self, team_key, year, model_type=None):
        matches = TeamYearMatchesQuery(self.team_key, int(year)).fetch(dict_version='3')
        if model_type is not None:
            matches = [{key: match[key] for key in match_properties[model_type]} for match in matches]

        return json.dumps(matches, ensure_ascii=True)


class ApiTeamEventAwardsController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_event_awards_controller_{}_{}"  # (team_key, event_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60

    def __init__(self, *args, **kw):
        super(ApiTeamEventAwardsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.event_key = self.request.route_kwargs["event_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.event_key)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key), ("event_id_validator", self.event_key)]

    def _track_call(self, team_key, event_key):
        self._track_call_defer('team/event/awards', '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key):
        awards = TeamEventAwardsQuery(self.team_key, self.event_key).fetch(dict_version='3')

        return json.dumps(awards, ensure_ascii=True)


class ApiTeamYearAwardsController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_year_awards_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60

    def __init__(self, *args, **kw):
        super(ApiTeamYearAwardsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = self.request.route_kwargs["year"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _track_call(self, team_key, year):
        self._track_call_defer('team/year/awards', '{}/{}'.format(team_key, year))

    def _render(self, team_key, year):
        awards = TeamYearAwardsQuery(self.team_key, int(year)).fetch(dict_version='3')

        return json.dumps(awards, ensure_ascii=True)


class ApiTeamHistoryAwardsController(ApiTeamControllerBase):
    """
    Returns a JSON list of award models won by a team
    """
    CACHE_KEY_FORMAT = "apiv3_team_history_awards_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryAwardsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/awards', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        awards = TeamAwardsQuery(self.team_key).fetch(dict_version='3')

        return json.dumps(awards, ensure_ascii=True)


class ApiTeamYearMediaController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv3_team_year_media_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamYearMediaController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = self.request.route_kwargs.get("year")
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    def _track_call(self, team_key, year):
        api_label = team_key
        api_label += '/{}'.format(year)
        self._track_call_defer('team/media', api_label)

    def _render(self, team_key, year):
        self._set_team(team_key)

        medias = TeamYearMediaQuery(self.team_key, int(year)).fetch(dict_version='3')

        return json.dumps(medias, ensure_ascii=True)
