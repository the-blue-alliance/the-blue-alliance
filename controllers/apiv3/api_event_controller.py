import json

from google.appengine.ext import ndb

from controllers.apiv3.api_base_controller import ApiBaseController
from controllers.apiv3.model_properties import filter_event_properties, filter_team_properties, filter_match_properties
from database.award_query import EventAwardsQuery
from database.event_query import EventQuery, EventListQuery
from database.event_details_query import EventDetailsQuery
from database.match_query import EventMatchesQuery
from database.team_query import EventTeamsQuery
from models.event_team import EventTeam


class ApiEventListController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, year, model_type=None):
        action = 'event/list'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, year)

    def _render(self, year, model_type=None):
        events, self._last_modified = EventListQuery(int(year)).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            events = filter_event_properties(events, model_type)
        return json.dumps(events, ensure_ascii=True, indent=True, sort_keys=True)


class ApiEventController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key, model_type=None):
        action = 'event'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, event_key)

    def _render(self, event_key, model_type=None):
        event, self._last_modified = EventQuery(event_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            event = filter_event_properties([event], model_type)[0]

        return json.dumps(event, ensure_ascii=True, indent=2, sort_keys=True)


class ApiEventDetailsController(ApiBaseController):
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key, detail_type):
        action = 'event/{}'.format(detail_type)
        self._track_call_defer(action, event_key)

    def _add_alliance_status(self, event_key, alliances):
        captain_team_keys = []
        for alliance in alliances:
            if alliance['picks']:
                captain_team_keys.append(alliance['picks'][0])

        event_team_keys = [ndb.Key(EventTeam, "{}_{}".format(event_key, team_key)) for team_key in captain_team_keys]
        captain_eventteams_future = ndb.get_multi_async(event_team_keys)
        for captain_future, alliance in zip(captain_eventteams_future, alliances):
            captain = captain_future.get_result()
            if captain and captain.status and 'alliance' in captain.status and 'playoff' in captain.status:
                alliance['status'] = captain.status['playoff']
            else:
                alliance['status'] = 'unknown'
        return alliances

    def _render(self, event_key, detail_type):
        event_details, self._last_modified = EventDetailsQuery(event_key).fetch(dict_version=3, return_updated=True)
        if detail_type == 'alliances' and event_details[detail_type]:
            data = self._add_alliance_status(event_key, event_details[detail_type])
        else:
            data = event_details[detail_type]

        return json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True)


class ApiEventTeamsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key, model_type=None):
        action = 'event/teams'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, event_key)

    def _render(self, event_key, model_type=None):
        teams, self._last_modified = EventTeamsQuery(event_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            teams = filter_team_properties(teams, model_type)

        return json.dumps(teams, ensure_ascii=True, indent=2, sort_keys=True)


class ApiEventMatchesController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key, model_type=None):
        action = 'event/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, event_key)

    def _render(self, event_key, model_type=None):
        matches, self._last_modified = EventMatchesQuery(event_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            matches = filter_match_properties(matches, model_type)

        return json.dumps(matches, ensure_ascii=True, indent=2, sort_keys=True)


class ApiEventAwardsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key):
        self._track_call_defer('event/awards', event_key)

    def _render(self, event_key):
        awards, self._last_modified = EventAwardsQuery(event_key).fetch(dict_version=3, return_updated=True)

        return json.dumps(awards, ensure_ascii=True, indent=2, sort_keys=True)
