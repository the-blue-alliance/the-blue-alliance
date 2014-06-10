from google.appengine.ext import ndb

from controllers.api.api_team_controller import ApiTeamController, ApiTeamMediaController
from controllers.api.api_event_controller import ApiEventController, ApiEventTeamsController, \
                                                 ApiEventMatchesController, ApiEventStatsController, \
                                                 ApiEventRankingsController, ApiEventAwardsController, ApiEventListController

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class CacheClearer(object):
    @classmethod
    def clear_award_and_references(cls, affected_refs):
        """
        Clears cache for controllers that references this award
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team_list']
        years = affected_refs['year']

        cls._clear_event_awards_controllers(event_keys)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_event_and_references(cls, affected_refs):
        """
        Clears cache for controllers that references this event
        """
        event_keys = affected_refs['key']
        years = affected_refs['year']

        event_team_keys_future = EventTeam.query(EventTeam.event.IN([event_key for event_key in event_keys])).fetch_async(None, keys_only=True)

        team_keys = set()
        for et_key in event_team_keys_future.get_result():
            team_key_name = et_key.id().split('_')[1]
            team_keys.add(ndb.Key(Team, team_key_name))

        cls._clear_events_controllers(event_keys)
        cls._clear_eventlist_controllers(years)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_eventteam_and_references(cls, affected_refs):
        """
        Clears cache for controllers that references this eventteam
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team']
        years = affected_refs['year']

        cls._clear_eventteams_controllers(event_keys)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_match_and_references(cls, affected_refs):
        """
        Clears cache for controllers that references this match
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team_keys']
        years = affected_refs['year']

        cls._clear_matches_controllers(event_keys)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_media_and_references(cls, affected_refs):
        """
        Clears cache for controllers that reference this media
        """
        reference_keys = affected_refs['references']
        years = affected_refs['year']

        cls._clear_media_controllers(reference_keys, years)

    @classmethod
    def clear_team_and_references(cls, affected_refs):
        """
        Clears cache for controllers that references this team
        """
        team_keys = affected_refs['key']

        event_team_keys_future = EventTeam.query(EventTeam.team.IN([team_key for team_key in team_keys])).fetch_async(None, keys_only=True)

        event_keys = set()
        years = set()
        for et_key in event_team_keys_future.get_result():
            event_key_name = et_key.id().split('_')[0]
            event_keys.add(ndb.Key(Event, event_key_name))
            years.add(int(event_key_name[:4]))

        cls._clear_teams_controllers(team_keys, years)
        cls._clear_eventteams_controllers(event_keys)

    @classmethod
    def _clear_event_awards_controllers(cls, event_keys):
        for event_key in filter(None, event_keys):
            ApiEventAwardsController.clear_cache(event_key.id())

    @classmethod
    def _clear_events_controllers(cls, event_keys):
        for event_key in filter(None, event_keys):
            ApiEventController.clear_cache(event_key.id())
            ApiEventStatsController.clear_cache(event_key.id())
            ApiEventRankingsController.clear_cache(event_key.id())

    @classmethod
    def _clear_eventlist_controllers(cls, years):
        for year in filter(None, years):
            ApiEventListController.clear_cache(year)

    @classmethod
    def _clear_eventteams_controllers(cls, event_keys):
        for event_key in filter(None, event_keys):
            ApiEventTeamsController.clear_cache(event_key.id())

    @classmethod
    def _clear_matches_controllers(cls, event_keys):
        for event_key in filter(None, event_keys):
            ApiEventMatchesController.clear_cache(event_key.id())

    @classmethod
    def _clear_media_controllers(cls, team_keys, years):
        for team_key in filter(None, team_keys):
            for year in filter(None, years):
                ApiTeamMediaController.clear_cache(team_key.id(), year)

    @classmethod
    def _clear_teams_controllers(cls, team_keys, years):
        for team_key in filter(None, team_keys):
            for year in filter(None, years):
                ApiTeamController.clear_cache(team_key.id(), year)
