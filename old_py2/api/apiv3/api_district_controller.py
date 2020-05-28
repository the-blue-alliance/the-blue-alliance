import json

from google.appengine.ext import ndb

from api.apiv3.api_base_controller import ApiBaseController
from api.apiv3.model_properties import filter_event_properties, filter_team_properties
from database.district_query import DistrictQuery, DistrictChampsInYearQuery, DistrictsInYearQuery
from database.event_query import DistrictEventsQuery
from database.team_query import DistrictTeamsQuery


class ApiDistrictListController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, year):
        self._track_call_defer('district/list', year)

    def _render(self, year):
        district_list, self._last_modified = DistrictsInYearQuery(int(year)).fetch(dict_version=3, return_updated=True)
        return json.dumps(district_list, ensure_ascii=True, indent=True, sort_keys=True)


class ApiDistrictEventsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, district_key, model_type=None):
        action = 'district/events'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}'.format(district_key))

    def _render(self, district_key, model_type=None):
        events, self._last_modified = DistrictEventsQuery(district_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            events = filter_event_properties(events, model_type)
        return json.dumps(events, ensure_ascii=True, indent=True, sort_keys=True)


class ApiDistrictTeamsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, district_key, model_type=None):
        action = 'district/teams'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}'.format(district_key))

    def _render(self, district_key, model_type=None):
        teams, self._last_modified = DistrictTeamsQuery(district_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            teams = filter_team_properties(teams, model_type)
        return json.dumps(teams, ensure_ascii=True, indent=True, sort_keys=True)


class ApiDistrictRankingsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, district_key, model_type=None):
        action = 'district/rankings'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}'.format(district_key))

    def _render(self, district_key, model_type=None):
        district, self._last_modified = DistrictQuery(district_key).fetch(return_updated=True)
        return json.dumps(district.rankings, ensure_ascii=True, indent=True, sort_keys=True)
