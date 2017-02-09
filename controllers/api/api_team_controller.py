import json
import webapp2

from datetime import datetime

from google.appengine.ext import ndb

from controllers.api.api_base_controller import ApiBaseController

from database.award_query import TeamAwardsQuery, TeamEventAwardsQuery
from database.event_query import TeamEventsQuery, TeamYearEventsQuery
from database.match_query import TeamEventMatchesQuery
from database.media_query import TeamYearMediaQuery
from database.robot_query import TeamRobotsQuery
from database.team_query import TeamListQuery, TeamParticipationQuery, TeamDistrictsQuery
from helpers.award_helper import AwardHelper
from helpers.model_to_dict import ModelToDict
from helpers.data_fetchers.team_details_data_fetcher import TeamDetailsDataFetcher
from helpers.media_helper import MediaHelper

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
    CACHE_KEY_FORMAT = "apiv2_team_controller_{}"  # (team_key)
    CACHE_VERSION = 5
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        team_dict = ModelToDict.teamConverter(self.team)

        return json.dumps(team_dict, ensure_ascii=True)


class ApiTeamEventsController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_events_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 60 * 60

    def __init__(self, *args, **kw):
        super(ApiTeamEventsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team/events', api_label)

    def _render(self, team_key, year=None):
        self._set_team(team_key)

        events = TeamYearEventsQuery(self.team_key, self.year).fetch()

        events = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(events, ensure_ascii=True)


class ApiTeamEventAwardsController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_event_awards_controller_{}_{}"  # (team_key, event_key)
    CACHE_VERSION = 4
    CACHE_HEADER_LENGTH = 60 * 60

    def __init__(self, *args, **kw):
        super(ApiTeamEventAwardsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.event_key = self.request.route_kwargs["event_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.event_key)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key), ("event_id_validator", self.event_key)]

    def _track_call(self, team_key, event_key):
        self._track_call_defer('team/event/awards', '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key):
        awards = TeamEventAwardsQuery(self.team_key, self.event_key).fetch()

        awards_dicts = [ModelToDict.awardConverter(award) for award in AwardHelper.organizeAwards(awards)]

        return json.dumps(awards_dicts, ensure_ascii=True)


class ApiTeamEventMatchesController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_event_matches_controller_{}_{}"  # (team_key, event_key)
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiTeamEventMatchesController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.event_key = self.request.route_kwargs["event_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.event_key)

    @property
    def _validators(self):
        return [("team_id_validator", self.team_key), ("event_id_validator", self.event_key)]

    def _track_call(self, team_key, event_key):
        self._track_call_defer('team/event/matches', '{}/{}'.format(team_key, event_key))

    def _render(self, team_key, event_key):
        matches = TeamEventMatchesQuery(self.team_key, self.event_key).fetch()

        matches = [ModelToDict.matchConverter(match) for match in matches]

        return json.dumps(matches, ensure_ascii=True)


class ApiTeamMediaController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_media_controller_{}_{}"  # (team_key, year)
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamMediaController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self.year = int(self.request.route_kwargs.get("year") or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key, self.year)

    def _track_call(self, team_key, year=None):
        api_label = team_key
        if year is not None:
            api_label += '/{}'.format(year)
        self._track_call_defer('team/media', api_label)

    def _render(self, team_key, year=None):
        self._set_team(team_key)

        medias = TeamYearMediaQuery(self.team_key, self.year).fetch()

        media_list = [ModelToDict.mediaConverter(media) for media in medias]
        return json.dumps(media_list, ensure_ascii=True)


class ApiTeamYearsParticipatedController(ApiTeamControllerBase):
    CACHE_KEY_FORMAT = "apiv2_team_years_participated_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamYearsParticipatedController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs["team_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/years_participated', team_key)

    def _render(self, team_key):
        years_participated = sorted(TeamParticipationQuery(self.team_key).fetch())

        return json.dumps(years_participated, ensure_ascii=True)


class ApiTeamListController(ApiTeamControllerBase):
    """
    Returns a JSON list of teams, paginated by team number in sets of 500
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    CACHE_KEY_FORMAT = "apiv2_team_list_controller_{}"  # (page_num)
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 60 * 60 * 24
    PAGE_SIZE = 500

    def __init__(self, *args, **kw):
        super(ApiTeamListController, self).__init__(*args, **kw)
        self.page_num = self.request.route_kwargs['page_num']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.page_num)

    @property
    def _validators(self):
        return []

    def _track_call(self, page_num):
        self._track_call_defer('team/list', page_num)

    def _render(self, page_num):
        teams = TeamListQuery(int(page_num)).fetch()

        team_list = [ModelToDict.teamConverter(team) for team in teams]
        return json.dumps(team_list, ensure_ascii=True)


class ApiTeamHistoryEventsController(ApiTeamControllerBase):
    """
    Returns a JSON list of event models of all events attended by a team
    """
    CACHE_KEY_FORMAT = "apiv2_team_history_events_controller_{}"  # (team_key)
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryEventsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/events', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        events = TeamEventsQuery(self.team_key).fetch()

        event_list = [ModelToDict.eventConverter(event) for event in events]
        return json.dumps(event_list, ensure_ascii=True)


class ApiTeamHistoryAwardsController(ApiTeamControllerBase):
    """
    Returns a JSON list of award models won by a team
    """
    CACHE_KEY_FORMAT = "apiv2_team_history_awards_controller_{}"  # (team_key)
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryAwardsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/awards', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        awards = TeamAwardsQuery(self.team_key).fetch()

        awards_list = [ModelToDict.awardConverter(award) for award in awards]
        return json.dumps(awards_list, ensure_ascii=True)


class ApiTeamHistoryRobotsController(ApiTeamControllerBase):
    """
    Returns a JSON list of all robot models associated with a Team
    """
    CACHE_KEY_FORMAT = "apiv2_team_history_robots_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryRobotsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/robots', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        robots = TeamRobotsQuery(self.team_key).fetch()

        robots_dict = {robot.year: ModelToDict.robotConverter(robot) for robot in robots}
        return json.dumps(robots_dict, ensure_ascii=True)


class ApiTeamHistoryDistrictsController(ApiTeamControllerBase):
    """
    Returns a mapping of year: district_key for a Team
    """
    CACHE_KEY_FORMAT = "apiv2_team_history_districts_controller_{}"  # (team_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiTeamHistoryDistrictsController, self).__init__(*args, **kw)
        self.team_key = self.request.route_kwargs['team_key']
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.team_key)

    def _track_call(self, team_key):
        self._track_call_defer('team/history/districts', team_key)

    def _render(self, team_key):
        self._set_team(team_key)

        districts = TeamDistrictsQuery(self.team_key).fetch()

        ret = {district.year: district.key.id() for district in districts}
        return json.dumps(ret, ensure_ascii=True)
