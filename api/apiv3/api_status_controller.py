import json

from api.apiv3.api_base_controller import ApiBaseController

from models.sitevar import Sitevar


class ApiStatusController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self):
        self._track_call_defer('status', 'status')

    def _render(self):
        status_sitevar_future = Sitevar.get_by_id_async('apistatus')
        fmsapi_sitevar_future = Sitevar.get_by_id_async('apistatus.fmsapi_down')
        down_events_sitevar_future = Sitevar.get_by_id_async('apistatus.down_events')

        # Error out of no sitevar found
        status_sitevar = status_sitevar_future.get_result()
        if not status_sitevar:
            self._errors = {"404": "API Status Not Found"}
            self.abort(404)

        status_dict = status_sitevar.contents
        down_events_sitevar = down_events_sitevar_future.get_result()
        down_events_list = down_events_sitevar.contents if down_events_sitevar else None

        fmsapi_sitevar = fmsapi_sitevar_future.get_result()
        status_dict['is_datafeed_down'] = True if fmsapi_sitevar and fmsapi_sitevar.contents == True else False
        status_dict['down_events'] = down_events_list if down_events_list is not None else []

        last_modified_times = [status_sitevar.updated]
        if down_events_sitevar:
            last_modified_times.append(down_events_sitevar.updated)
        if fmsapi_sitevar:
            last_modified_times.append(fmsapi_sitevar.updated)

        self._last_modified = max(last_modified_times)

        return json.dumps(status_dict, ensure_ascii=True, indent=2, sort_keys=True)
