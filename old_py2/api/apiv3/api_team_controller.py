import datetime
import json

from google.appengine.ext import ndb

from consts.media_tag import MediaTag

from api.apiv3.api_base_controller import ApiBaseController
from api.apiv3.model_properties import filter_event_properties, filter_team_properties, filter_match_properties
from database.award_query import TeamAwardsQuery, TeamYearAwardsQuery, TeamEventAwardsQuery
from database.event_query import TeamEventsQuery, TeamYearEventsQuery, TeamYearEventTeamsQuery
from database.match_query import TeamEventMatchesQuery, TeamYearMatchesQuery
from database.media_query import TeamYearMediaQuery, TeamSocialMediaQuery, TeamTagMediasQuery, TeamYearTagMediasQuery
from database.team_query import TeamQuery, TeamListQuery, TeamListYearQuery, TeamParticipationQuery, TeamDistrictsQuery
from database.robot_query import TeamRobotsQuery
from helpers.event_team_status_helper import EventTeamStatusHelper
from models.event_team import EventTeam
from models.team import Team


class ApiTeamListAllController(ApiBaseController):
    CACHE_VERSION = 0
    # `all` endpoints have a longer-than-usual edge cache of one hour
    CACHE_HEADER_LENGTH = 60 * 60

    def _track_call(self, model_type=None):
        action = 'team/list'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, 'all')

    def _render(self, model_type=None):
        max_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
        max_team_num = int(max_team_key.id()[3:])
        max_team_page = int(max_team_num / 500)

        futures = []
        for page_num in xrange(max_team_page + 1):
            futures.append(TeamListQuery(page_num).fetch_async(dict_version=3, return_updated=True))

        team_list = []
        for future in futures:
            partial_team_list, last_modified = future.get_result()
            team_list += partial_team_list
            if self._last_modified is None or last_modified > self._last_modified:
                self._last_modified = last_modified

        if model_type is not None:
            team_list = filter_team_properties(team_list, model_type)
        return json.dumps(team_list, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamListController(ApiBaseController):
    """
    Returns a JSON list of teams, paginated by team number in sets of 500
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61
    PAGE_SIZE = 500

    def _track_call(self, page_num, year=None, model_type=None):
        action = 'team/list'
        if year:
            action += '/{}'.format(year)
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, page_num)

    def _render(self, page_num, year=None, model_type=None):
        if year is None:
            team_list, self._last_modified = TeamListQuery(int(page_num)).fetch(dict_version=3, return_updated=True)
        else:
            team_list, self._last_modified = TeamListYearQuery(int(year), int(page_num)).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            team_list = filter_team_properties(team_list, model_type)
        return json.dumps(team_list, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, model_type=None):
        action = 'team'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, team_key)

    def _render(self, team_key, model_type=None):
        team, self._last_modified = TeamQuery(team_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            team = filter_team_properties([team], model_type)[0]

        return json.dumps(team, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamYearsParticipatedController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key):
        self._track_call_defer('team/years_participated', team_key)

    def _render(self, team_key):
        years_participated, self._last_modified = TeamParticipationQuery(team_key).fetch(return_updated=True)
        years_participated = sorted(years_participated)

        return json.dumps(years_participated, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamHistoryDistrictsController(ApiBaseController):
    """
    Returns a JSON list of all DistrictTeam models associated with a Team
    """
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key):
        self._track_call_defer('team/history/districts', team_key)

    def _render(self, team_key):
        team_districts, self._last_modified = TeamDistrictsQuery(team_key).fetch(dict_version=3, return_updated=True)

        return json.dumps(team_districts, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamHistoryRobotsController(ApiBaseController):
    """
    Returns a JSON list of all robot models associated with a Team
    """
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key):
        self._track_call_defer('team/history/robots', team_key)

    def _render(self, team_key):
        robots, self._last_modified = TeamRobotsQuery(team_key).fetch(dict_version=3, return_updated=True)

        return json.dumps(robots, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamEventsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, year=None, model_type=None):
        api_label = team_key
        if year:
            api_label += '/{}'.format(year)
        action = 'team/events'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, api_label)

    def _render(self, team_key, year=None, model_type=None):
        if year:
            events, self._last_modified = TeamYearEventsQuery(team_key, int(year)).fetch(dict_version=3, return_updated=True)
        else:
            events, self._last_modified = TeamEventsQuery(team_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            events = filter_event_properties(events, model_type)
        return json.dumps(events, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamEventMatchesController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, event_key, model_type=None):
        action = 'team/event/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key, model_type=None):
        matches, self._last_modified = TeamEventMatchesQuery(team_key, event_key).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            matches = filter_match_properties(matches, model_type)

        return json.dumps(matches, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamYearMatchesController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, year, model_type=None):
        action = 'team/year/matches'
        if model_type:
            action += '/{}'.format(model_type)
        self._track_call_defer(action, '{}/{}'.format(team_key, year))

    def _render(self, team_key, year, model_type=None):
        matches, self._last_modified = TeamYearMatchesQuery(team_key, int(year)).fetch(dict_version=3, return_updated=True)
        if model_type is not None:
            matches = filter_match_properties(matches, model_type)

        return json.dumps(matches, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamEventAwardsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60

    def _track_call(self, team_key, event_key):
        self._track_call_defer('team/event/awards', '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key):
        awards, self._last_modified = TeamEventAwardsQuery(team_key, event_key).fetch(dict_version=3, return_updated=True)

        return json.dumps(awards, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamEventStatusController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, event_key):
        self._track_call_defer('team/event/status', '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key):
        event_team = EventTeam.get_by_id('{}_{}'.format(event_key, team_key))
        status = None
        if event_team:
            status = event_team.status
            self._last_modified = event_team.updated
        else:
            self._last_modified = datetime.datetime.now()
        if status:
            status.update({
                'alliance_status_str': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team_key, status),
                'playoff_status_str': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team_key, status),
                'overall_status_str': EventTeamStatusHelper.generate_team_at_event_status_string(team_key, status),
            })
        return json.dumps(status, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamYearEventsStatusesController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, year):
        self._track_call_defer('team/events/statuses', '{}/{}'.format(team_key, year))

    def _render(self, team_key, year):
        event_teams, self._last_modified = TeamYearEventTeamsQuery(team_key, int(year)).fetch(return_updated=True)
        statuses = {}
        for event_team in event_teams:
            status = event_team.status
            if status:
                status.update({
                    'alliance_status_str': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team_key, status),
                    'playoff_status_str': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team_key, status),
                    'overall_status_str': EventTeamStatusHelper.generate_team_at_event_status_string(team_key, status),
                })
            statuses[event_team.event.id()] = status
        return json.dumps(statuses, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamYearAwardsController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, year):
        self._track_call_defer('team/year/awards', '{}/{}'.format(team_key, year))

    def _render(self, team_key, year):
        awards, self._last_modified = TeamYearAwardsQuery(team_key, int(year)).fetch(dict_version=3, return_updated=True)

        return json.dumps(awards, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamHistoryAwardsController(ApiBaseController):
    """
    Returns a JSON list of award models won by a team
    """
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key):
        self._track_call_defer('team/history/awards', team_key)

    def _render(self, team_key):
        awards, self._last_modified = TeamAwardsQuery(team_key).fetch(dict_version=3, return_updated=True)

        return json.dumps(awards, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamYearMediaController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, year):
        api_label = team_key
        api_label += '/{}'.format(year)
        self._track_call_defer('team/media', api_label)

    def _render(self, team_key, year):
        medias, self._last_modified = TeamYearMediaQuery(team_key, int(year)).fetch(dict_version=3, return_updated=True)

        return json.dumps(medias, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamTagMediaController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key, tag, year=None):
        api_label = team_key
        api_label += '/{}'.format(tag)
        if year:
            api_label += '/{}'.format(year)
        self._track_call_defer('team/media/tag', api_label)

    def _render(self, team_key, tag, year=None):
        media_tag_enum = MediaTag.get_enum_from_url(tag)
        if year:
            medias, self._last_modified = TeamYearTagMediasQuery(team_key, int(year), media_tag_enum).fetch(dict_version=3, return_updated=True)
        else:
            medias, self._last_modified = TeamTagMediasQuery(team_key, media_tag_enum).fetch(dict_version=3, return_updated=True)

        return json.dumps(medias, ensure_ascii=True, indent=2, sort_keys=True)


class ApiTeamSocialMediaController(ApiBaseController):
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def _track_call(self, team_key):
        self._track_call_defer('team/social_media', team_key)

    def _render(self, team_key):
        social_medias, self._last_modified = TeamSocialMediaQuery(team_key).fetch(dict_version=3, return_updated=True)

        return json.dumps(social_medias, ensure_ascii=True, indent=2, sort_keys=True)
