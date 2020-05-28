import json

from api.apiv3.api_base_controller import ApiBaseController
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

        self._last_modified = zebra_data.updated
        return json.dumps(zebra_data.data, ensure_ascii=True, indent=2, sort_keys=True)
