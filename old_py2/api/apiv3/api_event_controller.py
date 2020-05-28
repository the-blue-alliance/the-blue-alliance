import json
import tba_config

from google.appengine.ext import ndb

from api.apiv3.api_base_controller import ApiBaseController
from api.apiv3.model_properties import filter_event_properties, filter_team_properties, filter_match_properties
from consts.playoff_type import PlayoffType
from database.award_query import EventAwardsQuery
from database.event_query import EventQuery, EventListQuery
from database.event_details_query import EventDetailsQuery
from database.match_query import EventMatchesQuery
from database.team_query import EventTeamsQuery, EventEventTeamsQuery
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.match_helper import MatchHelper
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from models.event_team import EventTeam
from models.match import Match


class ApiEventListAllController(ApiBaseController):
    CACHE_VERSION = 0
    # `all` endpoints have a longer-than-usual edge cache of one hour
    CACHE_HEADER_LENGTH = 60 * 60

    def _track_call(self, model_type=None):
        action = 'event/list'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, 'all')

    def _render(self, model_type=None):
        futures = []
        for year in tba_config.VALID_YEARS:
            futures.append(EventListQuery(year).fetch_async(dict_version=3, return_updated=True))

        events = []
        for future in futures:
            partial_events, last_modified = future.get_result()
            events += partial_events
            if self._last_modified is None or last_modified > self._last_modified:
                self._last_modified = last_modified

        if model_type is not None:
            events = filter_event_properties(events, model_type)
        return json.dumps(events, ensure_ascii=True, indent=True, sort_keys=True)


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


class ApiEventPlayoffAdvancementController(ApiBaseController):
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key):
        action = 'event/playoff_advancement'
        self._track_call_defer(action, event_key)

    def _render(self, event_key):
        event_future = EventQuery(event_key).fetch_async(return_updated=True)
        matches_future = EventMatchesQuery(event_key).fetch_async(return_updated=True)

        event, event_updated = event_future.get_result()
        event.prep_details()
        matches, matches_updated = matches_future.get_result()
        self._last_modified = max(event_updated, matches_updated)

        cleaned_matches = MatchHelper.deleteInvalidMatches(matches, event)
        matches = MatchHelper.organizeMatches(cleaned_matches)
        bracket_table = event.playoff_bracket
        playoff_advancement = event.playoff_advancement

        # Lazy handle the case when we haven't backfilled the event details
        if not bracket_table or not playoff_advancement:
            bracket_table2, playoff_advancement2, _, _ = PlayoffAdvancementHelper.generatePlayoffAdvancement(event, matches)
            bracket_table = bracket_table or bracket_table2
            playoff_advancement = playoff_advancement or playoff_advancement2

        output = []
        for level in Match.ELIM_LEVELS:
            level_ranks = []
            if playoff_advancement and playoff_advancement.get(level):
                if event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
                    level_ranks = PlayoffAdvancementHelper.transform2015AdvancementLevelForApi(event, playoff_advancement, level)
                else:
                    level_ranks = PlayoffAdvancementHelper.transformRoundRobinAdvancementLevelForApi(event, playoff_advancement, level)
            elif bracket_table and bracket_table.get(level):
                level_ranks = PlayoffAdvancementHelper.transformBracketLevelForApi(event, bracket_table, level)
            output.extend(level_ranks)

        return json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True)


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


class ApiEventTeamsStatusesController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, event_key):
        action = 'event/teams/statuses'
        self._track_call_defer(action, event_key)

    def _render(self, event_key):
        event_teams, self._last_modified = EventEventTeamsQuery(event_key).fetch(return_updated=True)
        statuses = {}
        for event_team in event_teams:
            status = event_team.status
            team_key = event_team.team.id()
            if status:
                status.update({
                    'alliance_status_str': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team_key, status),
                    'playoff_status_str': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team_key, status),
                    'overall_status_str': EventTeamStatusHelper.generate_team_at_event_status_string(team_key, status),
                })
            statuses[team_key] = status
        return json.dumps(statuses, ensure_ascii=True, indent=2, sort_keys=True)
