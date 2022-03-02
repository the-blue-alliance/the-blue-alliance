from typing import List, Tuple, Union

from google.appengine.api import memcache
from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.favorite import Favorite
from backend.common.models.team import Team
from backend.common.models.event_team import EventTeam


class TeamHelper(object):
    @classmethod
    def sort_teams(cls, team_list: List[Union[Team, None]]) -> List[Team]:
        """
        Takes a list of Teams (not a Query object).
        """
        filtered = filter(None, team_list)
        sorted_list = sorted(filtered, key=lambda team: team.team_number)

        return list(sorted_list)

    @classmethod
    def getPopularTeamsEvents(self, events: List[Event]) -> List[Tuple[Team, List[Event]]]:
        events_by_key = {}
        for event in events:
            events_by_key[event.key.id()] = event

        # Calculate popular teams
        # Get cached team keys
        event_team_keys = memcache.get_multi(events_by_key.keys(), namespace='event-team-keys')

        # Get uncached team keys
        to_query = set(events_by_key.keys()).difference(event_team_keys.keys())
        event_teams_futures = [(
            event_key,
            EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async(projection=[EventTeam.team])
        ) for event_key in to_query]

        # Merge cached and uncached team keys
        for event_key, event_teams in event_teams_futures:
            event_team_keys[event_key] = [et.team.id() for et in event_teams.get_result()]
        memcache.set_multi(event_team_keys, 60*60*24, namespace='event-team-keys')

        team_keys = []
        team_events = {}
        for event_key, event_team_keys in event_team_keys.items():
            team_keys += event_team_keys
            for team_key in event_team_keys:
                team_events[team_key] = events_by_key[event_key]

        # Get cached counts
        team_favorite_counts = memcache.get_multi(team_keys, namespace='team-favorite-counts')

        # Get uncached counts
        to_count = set(team_keys).difference(team_favorite_counts.keys())
        count_futures = [(
            team_key,
            Favorite.query(Favorite.model_key == team_key).count_async()
        ) for team_key in to_count]

        # Merge cached and uncached counts
        for team_key, count_future in count_futures:
            team_favorite_counts[team_key] = count_future.get_result()
        memcache.set_multi(team_favorite_counts, 60*60*24, namespace='team-favorite-counts')

        # Sort to get top popular teams
        popular_team_keys = []
        for team_key, _ in sorted(team_favorite_counts.items(), key=lambda tc: -tc[1])[:25]:
            popular_team_keys.append(ndb.Key(Team, team_key))
        popular_teams =  sorted(ndb.get_multi(popular_team_keys), key=lambda team: team.team_number)

        popular_teams_events = []
        for team in popular_teams:
            popular_teams_events.append((team, team_events[team.key.id()]))

        return popular_teams_events
