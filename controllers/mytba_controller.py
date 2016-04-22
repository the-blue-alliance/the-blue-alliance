import collections
import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.model_type import ModelType
from controllers.base_controller import LoggedInHandler
from database.event_query import EventListQuery, TeamYearEventsQuery
from database.team_query import EventTeamsQuery
from helpers.event_helper import EventHelper
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.team_helper import TeamHelper
from models.favorite import Favorite
from models.team import Team


class MyTBALiveController(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        user = self.user_bundle.account.key
        now = datetime.datetime.now()
        team_favorites_future = Favorite.query(Favorite.model_type == ModelType.TEAM, ancestor=user).fetch_async()

        live_events = EventHelper.getWeekEvents()
        favorite_team_keys = map(lambda f: ndb.Key(Team, f.model_key), team_favorites_future.get_result())
        favorite_teams_future = ndb.get_multi_async(favorite_team_keys)

        live_eventteams_futures = []
        for event in live_events:
            live_eventteams_futures.append(EventTeamsQuery(event.key_name).fetch_async())

        favorite_teams = [team_future.get_result() for team_future in favorite_teams_future]

        favorite_teams_events_futures = []
        for team in favorite_teams:
            favorite_teams_events_futures.append(TeamYearEventsQuery(team.key_name, now.year).fetch_async())

        live_events_with_teams = EventTeamStatusHelper.buildEventTeamStatus(live_events, live_eventteams_futures, favorite_teams)

        future_events_by_event = {}
        for team, events_future in zip(favorite_teams, favorite_teams_events_futures):
            events = events_future.get_result()
            if not events:
                continue
            EventHelper.sort_events(events)
            next_event = next((e for e in events if e.start_date > now), None)
            if next_event:
                if not next_event.key_name in future_events_by_event:
                    future_events_by_event[next_event.key_name] = (next_event, [])
                future_events_by_event[next_event.key_name][1].append(team)

        future_events_with_teams = []
        for event_key, data in future_events_by_event.iteritems():
            future_events_with_teams.append((data[0], TeamHelper.sortTeams(data[1])))

        self.template_values.update({
            'live_events_with_teams': live_events_with_teams,
            'future_events_with_teams': future_events_with_teams,
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/mytba_live.html')
        self.response.out.write(template.render(path, self.template_values))
