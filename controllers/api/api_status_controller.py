import json

from controllers.api.api_base_controller import ApiBaseController

from models.sitevar import Sitevar


class ApiStatusController(ApiBaseController):
    CACHE_KEY_FORMAT = "apiv2_status_controller"
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiStatusController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT

    @property
    def _validators(self):
        '''
        No validators for this endpoint
        '''
        return []

    def _track_call(self):
        self._track_call_defer('status', 'status')

    def _render(self):
        status_sitevar = Sitevar.get_by_id('apistatus')
        fmsapi_sitevar = Sitevar.get_by_id('apistatus.fmsapi_down')
        down_events_sitevar = Sitevar.get_by_id('apistatus.down_events')

        # Error out of no sitevar found
        if not status_sitevar:
            self._errors = json.dumps({"404": "API Status Not Found"})
            self.abort(404)

        status_dict = status_sitevar.contents
        down_events_list = down_events_sitevar.contents if down_events_sitevar else None

        status_dict['is_datafeed_down'] = True if fmsapi_sitevar and fmsapi_sitevar.contents == True else False
        status_dict['down_events'] = down_events_list if down_events_list is not None else []
        return json.dumps(status_dict, ensure_ascii=True)

    @classmethod
    def clear_cache_if_needed(cls, old_content, new_content):
        """
        Clears the cache associated with this response
        Only clears if old_content != new_content (e.g. response changes)
        """
        if old_content != new_content:
            cls.delete_cache_multi([cls.get_cache_key_from_format()])
