import json
import webapp2

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import filter_event_properties, filter_team_properties, filter_match_properties
# from database.award_query import TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery
from database.event_query import EventListQuery
# from database.match_query import TeamEventMatchesQuery, TeamYearMatchesQuery
# from database.media_query import TeamYearMediaQuery, TeamSocialMediaQuery
# from database.team_query import TeamQuery, TeamListQuery, TeamListYearQuery, TeamParticipationQuery, TeamDistrictsQuery
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
