import json
import webapp2

from google.appengine.ext import ndb

from datetime import datetime

from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher
from helpers.media_helper import MediaHelper

from models.media import Media
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

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team', api_label)

    def _render(self, team_key, year=None):
        self._set_cache_header_length(61)

        self.team = Team.get_by_id(self.team_key)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % self.team_key})
            self.abort(404)

        events_sorted, matches_by_event_key, awards_by_event_key, _ = TeamDetailsDataFetcher.fetch(self.team, self.year)
        team_dict = ModelToDict.teamConverter(self.team)

        team_dict["events"] = list()
        for event in events_sorted:
            event_dict = ModelToDict.eventConverter(event)
            event_dict["matches"] = [ModelToDict.matchConverter(match) for match in matches_by_event_key.get(event.key, [])]
            event_dict["awards"] = [ModelToDict.awardConverter(award) for award in awards_by_event_key.get(event.key, [])]
            team_dict["events"].append(event_dict)

        return json.dumps(team_dict, ensure_ascii=True)

class ApiTeamMediaController(ApiBaseController):

    CACHE_KEY_FORMAT = "apiv2_team_media_controller_{}_{}"  # (team, year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(ApiTeamMediaController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)     
        self._cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year) 
        self._track_call_defer('team/media', api_label)

    def _render(self, team_key, year=None):
        self.team = Team.get_by_id(team_key)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % team_key})
            self.abort(404) 

        if year is None:
            year = self.year
        else:
            year = int(year)
        
        media_keys = Media.query(Media.references == self.team.key, Media.year == year).fetch(500, keys_only=True)
        medias = ndb.get_multi(media_keys)
        media_list = [ModelToDict.mediaConverter(media) for media in medias] 
        return json.dumps(media_list, ensure_ascii=True)
