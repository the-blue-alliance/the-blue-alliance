from google.appengine.ext import ndb

from controllers.api.api_team_controller import ApiTeamController
from controllers.api.api_event_controller import ApiEventController, ApiEventTeamsController, \
                                                 ApiEventMatchesController, ApiEventStatsController, \
                                                 ApiEventRankingsController, ApiEventAwardsController, ApiEventListController

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class CacheClearer(object):
    @classmethod
    def clear_award_and_references(cls, event_keys, team_keys, years):
        """
        Clears cache for controllers that references this award
        """
        cls._clear_event_awards_controllers(event_keys)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_event_and_references(cls, event_keys, years):
        """
        Clears cache for controllers that references this event
        """
        event_team_keys_future = EventTeam.query(EventTeam.event.IN([event_key for event_key in event_keys])).fetch_async(None, keys_only=True)

        team_keys = set()
        for et_key in event_team_keys_future.get_result():
            team_key_name = et_key.id().split('_')[1]
            team_keys.add(ndb.Key(Team, team_key_name))

        cls._clear_events_controllers(event_keys, years)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_eventteam_and_references(cls, event_keys, team_keys, years):
        """
        Clears cache for controllers that references this eventteam
        """
        cls._clear_events_controllers(event_keys)
        cls._clear_eventteams_controllers(event_keys)
        cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_match_and_references(cls, match_keys, event_keys, team_keys, years):
        """
        Clears cache for controllers that references this match
        """
        cls._clear_matches_controllers(event_keys)
        for year in years:
            cls._clear_teams_controllers(team_keys, years)

    @classmethod
    def clear_team_and_references(cls, team_keys):
        """
        Clears cache for controllers that references this team
        """
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
        for event_key in event_keys:
            ApiEventAwardsController.clear_cache(event_key.id())

    @classmethod
    def _clear_events_controllers(cls, event_keys, years=set()):
        for event_key in event_keys:
            ApiEventController.clear_cache(event_key.id())
            ApiEventStatsController.clear_cache(event_key.id())
            ApiEventRankingsController.clear_cache(event_key.id())

        for year in years:
            ApiEventListController.clear_cache(year)

    @classmethod
    def _clear_eventteams_controllers(cls, event_keys):
        for event_key in event_keys:
            ApiEventTeamsController.clear_cache(event_key.id())

    @classmethod
    def _clear_matches_controllers(cls, event_keys):
        for event_key in event_keys:
            ApiEventMatchesController.clear_cache(event_key.id())

    @classmethod
    def _clear_teams_controllers(cls, team_keys, years):
        for team_key in team_keys:
            for year in years:
                ApiTeamController.clear_cache(team_key.id(), year)
