import json
import webapp2

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import filter_event_properties, filter_team_properties, filter_match_properties
# from database.award_query import TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery
from database.event_query import EventQuery, EventListQuery
from database.event_details_query import EventDetailsQuery
# from database.match_query import TeamEventMatchesQuery, TeamYearMatchesQuery
# from database.media_query import TeamYearMediaQuery, TeamSocialMediaQuery
from database.team_query import EventTeamsQuery
# from database.robot_query import TeamRobotsQuery


class ApiEventListController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, year, model_type=None):
        action = 'event/list'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, year)

    def _render(self, year, model_type=None):
        events, self._last_modified = EventListQuery(int(year)).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            events = filter_event_properties(events, model_type)
        return json.dumps(events, ensure_ascii=True, indent=True, sort_keys=True)


class ApiEventController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, event_key, model_type=None):
        action = 'event'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, event_key)

    def _render(self, event_key, model_type=None):
        event, self._last_modified = EventQuery(event_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            event = filter_event_properties([event], model_type)[0]

        return json.dumps(event, ensure_ascii=True, indent=2, sort_keys=True)


class ApiEventDetailsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key, detail_type):
        action = 'event/{}'.format(detail_type)
        self._track_call_defer(action, event_key)

    def _render(self, event_key, detail_type):
        event_details, self._last_modified = EventDetailsQuery(event_key).fetch(dict_version=3, return_updated=True)
        return json.dumps(event_details[detail_type], ensure_ascii=True, indent=2, sort_keys=True)


class ApiEventTeamsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, event_key, model_type=None):
        action = 'event/teams'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, event_key)

    def _render(self, event_key, model_type=None):
        teams, self._last_modified = EventTeamsQuery(event_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            teams = filter_team_properties(teams, model_type)

        return json.dumps(teams, ensure_ascii=True, indent=2, sort_keys=True)
