import json
import logging
import webapp2
import math
import numpy

from datetime import datetime
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

    def _set_event(self, event_key):
        self.event = Event.get_by_id(event_key)
        if self.event is None:
            self._errors = json.dumps({"404": "%s event not found" % self.event_key})
            self.abort(404)

    def _track_call(self, event_key):
        self._track_call_defer('event', event_key)

    def _render(self, event_key):
        self._set_cache_header_length(60 * 60)
        self._set_event(event_key)

        event_dict = ModelToDict.eventConverter(self.event)

        return json.dumps(event_dict, ensure_ascii=True)

class ApiEventTeamsController(ApiEventController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiEventTeamsController, self).__init__(*args, **kw)
        self._cache_key = "apiv2_event_teams_controller_{}".format(self.event_key)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_version = 2

    def _render(self, event_key):
        self._set_cache_header_length(60 * 60)
        self._set_event(event_key)

        teams = self.event.teams
        team_dicts = [ModelToDict.teamConverter(team) for team in teams]

        return json.dumps(team_dicts, ensure_ascii=True)

class ApiEventMatchesController(ApiEventController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiEventMatchesController, self).__init__(*args, **kw)
        self._cache_key = "apiv2_event_matches_controller_{}".format(self.event_key)
        self._cache_expiration = self.SHORT_CACHE_EXPIRATION
        self._cache_version = 2

    def _render(self, event_key):
        self._set_cache_header_length(61)
        self._set_event(event_key)

        matches = self.event.matches
        match_dicts = [ModelToDict.matchConverter(match) for match in matches]

        return json.dumps(match_dicts, ensure_ascii=True)


class ApiEventOprsController(ApiEventController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiEventOprsController, self).__init__(*args, **kw)
        self._cache_key = "apiv2_event_matches_controller_{}".format(self.event_key)
        self._cache_expiration = self.SHORT_CACHE_EXPIRATION
        self._cache_version = 2

    def _render(self, event_key):
        self._set_cache_header_length(61)
        self._set_event(event_key)

        oprs = [i for i in self.event.matchstats['oprs'].items()] if (self.event.matchstats is not None and 'oprs' in self.event.matchstats) else []
        sum_opr = 0
        num_oprs = 0
        just_oprs = []
        for opr in oprs:
            d = opr[1]
            sum_opr += d
            num_oprs += 1
            just_oprs.append(d)
        mean = sum_opr / num_oprs
        just_oprs = sorted(just_oprs)
        median = 0
        if len(just_oprs) % 2 == 0:
            median = (just_oprs[(len(just_oprs) / 2) - 1] + just_oprs[(len(just_oprs) / 2)]) / 2
        else:
            median = just_oprs[(len(just_oprs) / 2)]
        oprs = dict(sorted(oprs, key=lambda t: t[1], reverse=True))
        stdev = numpy.std(just_oprs)
        stats = {"median" : median, "stdev" : stdev, "mean" : mean}
        ret = {"stats" : stats, "oprs" : oprs}

        return json.dumps(ret, ensure_ascii=True)

class ApiEventListController(ApiBaseController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiEventListController, self).__init__(*args, **kw)
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_key = "apiv2_event_list_controller_{}".format(self.year)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_version = 2

    @property
    def _validators(self):
        return []

    def _track_call(self, *args, **kw):
        self._track_call_defer('event/list', self.year)

    def _render(self, year=None):
        self._set_cache_header_length(60 * 60 * 24 * 3)

        if self.year < 1992 or self.year > datetime.now().year + 1:
            self._errors = json.dumps({"404": "No events found for %s" % self.year})
            self.abort(404)

        event_keys = Event.query(Event.year == self.year).fetch(1000, keys_only=True)
        keys = [key.string_id() for key in event_keys]

        return json.dumps(keys, ensure_ascii=True)
