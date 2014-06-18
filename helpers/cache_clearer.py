from google.appengine.ext import ndb

from controllers.api.api_team_controller import ApiTeamController, ApiTeamMediaController, ApiTeamListController
from controllers.api.api_event_controller import ApiEventController, ApiEventTeamsController, \
                                                 ApiEventMatchesController, ApiEventStatsController, \
                                                 ApiEventRankingsController, ApiEventAwardsController, ApiEventListController

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class CacheClearer(object):
    @classmethod
    def get_award_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this award
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team_list']
        years = affected_refs['year']

        return cls._get_event_awards_cache_keys_and_controllers(event_keys) + \
            cls._get_teams_cache_keys_and_controllers(team_keys, years)

    @classmethod
    def get_event_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this event
        """
        event_keys = affected_refs['key']
        years = affected_refs['year']

        event_team_keys_future = EventTeam.query(EventTeam.event.IN([event_key for event_key in event_keys])).fetch_async(None, keys_only=True)

        team_keys = set()
        for et_key in event_team_keys_future.get_result():
            team_key_name = et_key.id().split('_')[1]
            team_keys.add(ndb.Key(Team, team_key_name))

        return cls._get_events_cache_keys_and_controllers(event_keys) + \
            cls._get_eventlist_cache_keys_and_controllers(years) + \
            cls._get_teams_cache_keys_and_controllers(team_keys, years)

    @classmethod
    def get_eventteam_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this eventteam
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team']
        years = affected_refs['year']

        return cls._get_eventteams_cache_keys_and_controllers(event_keys) + \
            cls._get_teams_cache_keys_and_controllers(team_keys, years)

    @classmethod
    def get_match_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this match
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team_keys']
        years = affected_refs['year']

        return cls._get_matches_cache_keys_and_controllers(event_keys) + \
            cls._get_teams_cache_keys_and_controllers(team_keys, years)

    @classmethod
    def get_media_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that reference this media
        """
        reference_keys = affected_refs['references']
        years = affected_refs['year']

        return cls._get_media_cache_keys_and_controllers(reference_keys, years)

    @classmethod
    def get_team_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this team
        """
        team_keys = affected_refs['key']

        event_team_keys_future = EventTeam.query(EventTeam.team.IN([team_key for team_key in team_keys])).fetch_async(None, keys_only=True)

        event_keys = set()
        years = set()
        for et_key in event_team_keys_future.get_result():
            event_key_name = et_key.id().split('_')[0]
            event_keys.add(ndb.Key(Event, event_key_name))
            years.add(int(event_key_name[:4]))

        return cls._get_teams_cache_keys_and_controllers(team_keys, years) + \
            cls._get_eventteams_cache_keys_and_controllers(event_keys) + \
            cls._get_teamlist_cache_keys_and_controllers(team_keys)

    @classmethod
    def _get_event_awards_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventAwardsController.get_full_cache_key(event_key.id()), ApiEventAwardsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_events_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventController.get_full_cache_key(event_key.id()), ApiEventController))
            cache_keys_and_controllers.append((ApiEventStatsController.get_full_cache_key(event_key.id()), ApiEventStatsController))
            cache_keys_and_controllers.append((ApiEventRankingsController.get_full_cache_key(event_key.id()), ApiEventRankingsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_eventlist_cache_keys_and_controllers(cls, years):
        cache_keys_and_controllers = []
        for year in filter(None, years):
            cache_keys_and_controllers.append((ApiEventListController.get_full_cache_key(year), ApiEventListController))
        return cache_keys_and_controllers

    @classmethod
    def _get_eventteams_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventTeamsController.get_full_cache_key(event_key.id()), ApiEventTeamsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_matches_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventMatchesController.get_full_cache_key(event_key.id()), ApiEventMatchesController))
        return cache_keys_and_controllers

    @classmethod
    def _get_media_cache_keys_and_controllers(cls, team_keys, years):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            for year in filter(None, years):
                cache_keys_and_controllers.append((ApiTeamMediaController.get_full_cache_key(team_key.id(), year), ApiTeamMediaController))
        return cache_keys_and_controllers

    @classmethod
    def _get_teams_cache_keys_and_controllers(cls, team_keys, years):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            for year in filter(None, years):
                cache_keys_and_controllers.append((ApiTeamController.get_full_cache_key(team_key.id(), year), ApiTeamController))
        return cache_keys_and_controllers

    @classmethod
    def _get_teamlist_cache_keys_and_controllers(cls, team_keys):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            page_num = int(team_key.id()[3:]) / ApiTeamListController.PAGE_SIZE
            cache_keys_and_controllers.append((ApiTeamListController.get_full_cache_key(page_num), ApiTeamListController))
        return cache_keys_and_controllers
