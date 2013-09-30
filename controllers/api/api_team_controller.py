import json
import logging
import webapp2

from datetime import datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb

import tba_config
from controllers.api.api_base_controller import ApiBaseController

from helpers.model_to_dict import ModelToDict

from models.award import Award
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class ApiTeamController(ApiBaseController):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(ApiTeamController, self).__init__(*args, **kw)
        self.team_id = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "team_detail_api_{}_{}".format(self.team_id, self.year)
        self._cache_version = 2

    @property
    def _validators(self):
        return [("team_id_validator", self.team_id)]

    def _render(self, team_key, year=None):

        @ndb.tasklet
        def get_event_matches_async(event_team_key):
            event_team = yield event_team_key.get_async()
            if (event_team.year == self.year):
                event = yield event_team.event.get_async()
                if not event.start_date:
                    event.start_date = datetime.datetime(self.year, 12, 31)  # unknown goes last
                matches_keys = yield Match.query(
                  Match.event == event.key, Match.team_key_names == self.team.key_name).fetch_async(500, keys_only=True)
                matches = yield ndb.get_multi_async(matches_keys)
                raise ndb.Return((event, matches))
            raise ndb.Return(None)

        @ndb.tasklet
        def get_events_matches_async():
            event_team_keys = yield EventTeam.query(EventTeam.team == self.team.key).fetch_async(1000, keys_only=True)
            events_matches = yield map(get_event_matches_async, event_team_keys)
            events_matches = filter(None, events_matches)
            raise ndb.Return(events_matches)

        @ndb.tasklet
        def get_awards_async():
            award_keys = yield Award.query(Award.year == self.year, Award.team == self.team.key).fetch_async(500, keys_only=True)
            awards = yield ndb.get_multi_async(award_keys)
            raise ndb.Return(awards)

        @ndb.toplevel
        def get_events_matches_awards():
            events_matches, awards = yield get_events_matches_async(), get_awards_async()
            raise ndb.Return(events_matches, awards)

        self.team = Team.get_by_id(self.team_id)
        if self.team is None:
            self._errors = json.dumps({"404": "%s team not found" % self.team_id})
            self.abort(404)
        events_matches, awards = get_events_matches_awards()
        events_matches = sorted(events_matches, key=lambda (e, _): e.start_date)
        team_dict = ModelToDict.teamConverter(self.team)


        team_dict["events"] = list()
        for event, matches in events_matches:
            event_dict = ModelToDict.eventConverter(event)
            event_dict["matches"] = [ModelToDict.matchConverter(match) for match in matches if match.event == event.key]
            event_dict["awards"] = [ModelToDict.awardConverter(award) for award in awards if award.event == event.key]
            team_dict["events"].append(event_dict)


        return json.dumps(team_dict, ensure_ascii=True)
