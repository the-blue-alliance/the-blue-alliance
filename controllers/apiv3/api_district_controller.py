import json

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import filter_event_properties, filter_team_properties
# from database.award_query import EventAwardsQuery
from database.event_query import DistrictEventsQuery
# from database.event_details_query import EventDetailsQuery
# from database.match_query import EventMatchesQuery
# from database.team_query import EventTeamsQuery


class ApiDistrictEventsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def _track_call(self, district_key, year, model_type=None):
        action = 'district/events'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(district_key, year))

    def _render(self, district_key, year, model_type=None):
        events, self._last_modified = DistrictEventsQuery('{}{}'.format(year, district_key)).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            events = filter_event_properties(events, model_type)
        return json.dumps(events, ensure_ascii=True, indent=True, sort_keys=True)
