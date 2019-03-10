import json
import logging

from collections import defaultdict
from api.apiv3.api_base_controller import ApiBaseController
from database.gdcv_data_query import MatchGdcvDataQuery, EventMatchesGdcvDataQuery
from database.event_query import EventQuery
from database.match_query import MatchQuery


class ApiRealtimeMatchController(ApiBaseController):

    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60  # One hour in seconds

    def _track_call(self, match_key):
        action = 'realtime_match'
        self._track_call_defer(action, match_key)

    def _render(self, match_key):
        match = MatchQuery(match_key).fetch()
        if not match:
            self.abort(404)
        if not match.has_been_played:
            # If FIRST hasn't published data yet, don't return anything
            return json.dumps([])

        match_key = match.key_name
        gdcv_data = MatchGdcvDataQuery(match_key).fetch()
        return json.dumps(gdcv_data, ensure_ascii=True, indent=2, sort_keys=True)


class ApiRealtimeEventMatchesController(ApiBaseController):

    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60  # One hour in seconds

    def _track_call(self, event_key):
        action = 'realtime_event_matches'
        self._track_call_defer(action, event_key)

    def _render(self, event_key):
        event = EventQuery(event_key).fetch()
        if not event:
            self.abort(404)
        event.get_matches_async()
        realtime_data = EventMatchesGdcvDataQuery(event.key_name).fetch()
        match_played_by_key = {
            m.key_name: m.has_been_played for m in event.matches
        }

        result = []
        for gdcv_item in realtime_data:
            match_key = "{}_{}".format(gdcv_item['event_key'], gdcv_item['match_id'])
            if match_played_by_key.get(match_key, False):
                result.append(match_key)
        return json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True)
