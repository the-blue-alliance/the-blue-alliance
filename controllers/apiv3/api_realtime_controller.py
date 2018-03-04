import json
import logging

from controllers.apiv3.api_base_controller import ApiBaseController
from database.gdcv_data_query import MatchGdcvDataQuery, EventMatchesGdcvDataQuery
from database.event_query import EventQuery
from database.match_query import MatchQuery


class ApiRealtimeMatchController(ApiBaseController):

    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

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

    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key):
        action = 'realtime_event_matches'
        self._track_call_defer(action, event_key)

    def _render(self, event_key):
        event = EventQuery(event_key).fetch()
        if not event:
            self.abort(404)
        event.get_matches_async()
        realtime_data = EventMatchesGdcvDataQuery(event.key_name).fetch()
        realtime_by_key = {
            "{}_{}".format(m['event_key'], m['match_id']): m
            for m in realtime_data
        }

        event_matches = event.matches
        result = {
            m.key_name: realtime_by_key[m.key_name]
            for m in event_matches
            if m.has_been_played and m.key_name in realtime_by_key
        }
        return json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True)
