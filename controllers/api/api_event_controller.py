import json
import logging
import webapp2

from datetime import datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb

import tba_config
from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict

from models.event import Event

class ApiEventController(ApiBaseController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiEventController, self).__init__(*args, **kw)
        self.event_key = self.request.route_kwargs["event_key"]
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "apiv2_event_controller_{}".format(self.event_key)
        self._cache_version = 2

    @property
    def _validators(self):
        return [("event_id_validator", self.event_key)]

    def _track_call(self, event_key):
        api_label = event_key
        self._track_call_defer('event', api_label)

    def _render(self, event_key):
        self._write_cache_headers(61)

        self.event = Event.get_by_id(self.event_key)
        if self.event is None:
            self._errors = json.dumps({"404": "%s event not found" % self.event_key})
            self.abort(404)

        event_dict = ModelToDict.eventConverter(self.event)

        return json.dumps(event_dict, ensure_ascii=True)
