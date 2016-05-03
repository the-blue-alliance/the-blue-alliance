import json
import webapp2

from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict

from models.match import Match


class ApiMatchControllerBase(ApiBaseController):

    def __init__(self, *args, **kw):
        super(ApiMatchControllerBase, self).__init__(*args, **kw)
        self.match_key = self.request.route_kwargs["match_key"]

    @property
    def _validators(self):
        return [("match_id_validator", self.match_key)]

    def _set_match(self, match_key):
        self.match = Match.get_by_id(match_key)
        if self.match is None:
            self._errors = json.dumps({"404": "%s match not found" % self.match_key})
            self.abort(404)


class ApiMatchController(ApiMatchControllerBase):

    CACHE_KEY_FORMAT = "apiv2_match_controller_{}"  # (match_key)
    CACHE_VERSION = 5
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiMatchController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.match_key)

    def _track_call(self, match_key):
        self._track_call_defer('match', match_key)

    def _render(self, match_key):
        self._set_match(match_key)

        match_dict = ModelToDict.matchConverter(self.match)

        return json.dumps(match_dict, ensure_ascii=True)
