import json

from google.appengine.ext import ndb

from api.apiv3.api_base_controller import ApiBaseController
from models.event import Event
from models.zebra_motionworks import ZebraMotionWorks


class ApiZebraMotionworksMatchController(ApiBaseController):

    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, match_key):
        action = 'zebra_motionworks_match'
        self._track_call_defer(action, match_key)

    def _render(self, match_key):
        zebra_data = ZebraMotionWorks.get_by_id(match_key)
        if not zebra_data:
            self.abort(404)

        return json.dumps(zebra_data.data, ensure_ascii=True, indent=2, sort_keys=True)


class ApiZebraMotionworksEventMatchesController(ApiBaseController):

    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key):
        action = 'zebra_motionworks_event_matches'
        self._track_call_defer(action, event_key)

    def _render(self, event_key):
        zebra_data = ZebraMotionWorks.query(ZebraMotionWorks.event == ndb.Key(Event, event_key)).fetch()
        if not zebra_data:
            self.abort(404)

        return json.dumps([data.data for data in zebra_data], ensure_ascii=True, indent=2, sort_keys=True)
