import json
import logging
import webapp2

from datetime import datetime

from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher

from models.team import Team


class ApiTeamController(ApiBaseController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiTeamController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "apiv2_team_controller_{}_{}".format(self.team_key, self.year)
        self._cache_version = 2

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key)]

    def _render(self, team_key, year=None):
        self._write_cache_headers(61)

        self.team = Team.get_by_id(self.team_key)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % self.team_key})
            self.abort(404)

        events_sorted, matches_by_event_key, awards_by_event_key, _ = TeamDetailsDataFetcher.fetch(self.team, self.year)
        team_dict = ModelToDict.teamConverter(self.team)

        team_dict["events"] = list()
        for e in events_sorted:
            event_dict = ModelToDict.eventConverter(e)
            event_dict["matches"] = [ModelToDict.matchConverter(match) for match in matches_by_event_key.get(e.key, [])]
            event_dict["awards"] = [ModelToDict.awardConverter(award) for award in awards_by_event_key.get(e.key, [])]
            team_dict["events"].append(event_dict)

        return json.dumps(team_dict, ensure_ascii=True)
