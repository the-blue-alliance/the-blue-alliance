import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher
from helpers.media_helper import MediaHelper

from models.media import Media
from models.event_team import EventTeam
from models.team import Team


class ApiTeamControllerBase(ApiBaseController):
    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _set_team(self, team_key):
        self.team = Team.get_by_id(team_key)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % team_key})
            self.abort(404)


class ApiTeamController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(ApiTeamController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team', api_label)

    def _render(self, team_key, year=None):
        self._set_team(team_key)

        team_dict = ModelToDict.teamConverter(self.team)

        return json.dumps(team_dict, ensure_ascii=True)


class ApiTeamEventsController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_events_controller_{}"  # (team_key, year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(ApiTeamEventsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team/events', api_label)

    def _render(self, team_key, year=None):
        self._set_team(team_key)

        event_team_keys = EventTeam.query(EventTeam.team == self.team.key, EventTeam.year == self.year).fetch(1000, keys_only=True)
        event_teams = ndb.get_multi(event_team_keys)
        event_keys = [event_team.event for event_team in event_teams]
        events = ndb.get_multi(event_keys)

        events = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(events, ensure_ascii=True)


class ApiTeamMediaController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_media_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(ApiTeamMediaController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team/media', api_label)

    def _render(self, team_key, year=None):
        self._set_team(team_key)

        media_keys = Media.query(Media.references == self.team.key, Media.year == self.year).fetch(500, keys_only=True)
        medias = ndb.get_multi(media_keys)
        media_list = [ModelToDict.mediaConverter(media) for media in medias]

        return json.dumps(media_list, ensure_ascii=True)
