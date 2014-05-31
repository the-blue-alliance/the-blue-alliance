import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class ApiTeamController(ApiBaseController):
    CACHE_KEY_FORMAT = "apiv2_team_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(ApiTeamController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _set_team(self, team_key):
        self.team = Team.get_by_id(team_key)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % team_key})
            self.abort(404)

    def _track_call(self, team_key, year=None, event_key=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team', api_label)

    def _render(self, team_key, year=None):
        self._set_cache_header_length(61)

        self._set_team(team_key)
        team_dict = ModelToDict.teamConverter(self.team) 

        return json.dumps(team_dict, ensure_ascii=True)


class ApiTeamEventsController(ApiTeamController):

    def __init__(self, *args, **kw):
        super(ApiTeamEventsController, self).__init__(*args, **kw)
        self._cache_key = "apiv2_team_events_controller_{}".format(self.team_key)
        self._cache_version = 2

    def _render(self, team_key, year=None):
        self._set_cache_header_length(61)
        self._set_team(team_key)

        event_team_keys = EventTeam.query(EventTeam.team == self.team.key,
                                          EventTeam.year == self.year)\
                                   .fetch(1000, keys_only=True)
        event_teams = ndb.get_multi(event_team_keys)
        event_keys = [event_team.event for event_team in event_teams]
        events = ndb.get_multi(event_keys)

        events = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(events, ensure_ascii=True)


class ApiTeamMatchesController(ApiTeamController):

    def __init__(self, *args, **kw):
        super(ApiTeamMatchesController, self).__init__(*args, **kw)
        self.event_key = self.request.route_kwargs.get("event_key")
        self._cache_key = "apiv2_team_matches_controller_{}".format(self.team_key)
        self._cache_version = 2


    def validators(self):
        if self.event_key is not None: return [('event_id_validator', self.event_key)]

    def _render(self, team_key, year=None, event_key=None):
        self._set_cache_header_length(61)
        self._set_team(team_key)

        if event_key is not None:
            event_team_keys = EventTeam.query(EventTeam.team == self.team.key,
                                              EventTeam.year == self.year,
                                              EventTeam.event == ndb.Key(Event, event_key))\
                                       .fetch(1000, keys_only=True)
        else:
            event_team_keys = EventTeam.query(EventTeam.team == self.team.key,
                                              EventTeam.year == self.year)\
                                       .fetch(1000, keys_only=True)

        event_keys = ndb.get_multi(event_team_keys)
        events = [event.event for event in event_keys]
        team_matches = Match.query(Match.team_key_names == self.team.key_name, Match.event.IN(events)).fetch(1000)
        matches = [ModelToDict.matchConverter(match) for match in team_matches]

        return json.dumps(matches, ensure_ascii=True)


