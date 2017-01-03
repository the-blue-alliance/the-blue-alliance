import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import team_properties
from database.team_query import TeamListQuery, TeamListYearQuery
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
