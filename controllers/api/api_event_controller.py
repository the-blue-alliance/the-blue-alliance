import json
import logging
import webapp2

from google.appengine.ext import ndb

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

    def set_event(self):
        event = Event.get_by_id(self.event_key)
        if event is None:
            self._errors = json.dumps({"404": "%s event not found" % self.event_key})
            self.abort(404)
        self.event = event


    def _track_call(self, event_key):
        self._track_call_defer('event', event_key)

    def _render(self, event_key):
        self._set_cache_header_length(60 * 60)
        self.set_event()

        event_dict = ModelToDict.eventConverter(self.event)

        return json.dumps(event_dict, ensure_ascii=True)

class ApiEventTeamController(ApiEventController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiEventTeamController, self).__init__(*args, **kw)
        self._cache_key = "apiv2_event_team_controller_{}".format(self.event_key)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_version = 2

    def _render(self, event_key):
        self._set_cache_header_length(60 * 60)
        self.set_event()

        teams = self.event.teams
        team_dicts = list()
        for team in teams:
            team_dicts.append(ModelToDict.teamConverter(team))

        return json.dumps(team_dicts, ensure_ascii=True)

class ApiEventMatchController(ApiEventController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiEventMatchController, self).__init__(*args, **kw)
        self._cache_key = "apiv2_event_match_controller_{}".format(self.event_key)
        self._cache_expiration = self.SHORT_CACHE_EXPIRATION
        self._cache_version = 2


    def _render(self, event_key):
        self._set_cache_header_length(61)
        self.set_event()

        matches = self.event.matches
        match_dicts = list()
        for match in matches:
            match_dicts.append(ModelToDict.matchConverter(match))

        return json.dumps(match_dicts, ensure_ascii=True)
