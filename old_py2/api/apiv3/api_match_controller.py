import json

from google.appengine.ext import ndb

from api.apiv3.api_base_controller import ApiBaseController
from api.apiv3.model_properties import filter_match_properties
from database.match_query import MatchQuery


class ApiMatchController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, match_key, model_type=None):
        action = 'match'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, match_key)

    def _render(self, match_key, model_type=None):
        match, self._last_modified = MatchQuery(match_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            match = filter_match_properties([match], model_type)[0]

        return json.dumps(match, ensure_ascii=True, indent=2, sort_keys=True)
