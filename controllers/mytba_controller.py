import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.model_type import ModelType
from controllers.base_controller import LoggedInHandler
from database.event_query import EventListQuery
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
        all_events_this_year_future = EventListQuery(now.year).fetch_async()
        favorite_team_keys = map(lambda f: ndb.Key(Team, f.model_key), team_favorites_future.get_result())
        favorite_teams_future = ndb.get_multi_async(favorite_team_keys)

        future_events = filter(lambda e: e.start_date > now, all_events_this_year_future.get_result())
        future_eventteams_futures = []
        for event in future_events:
            future_eventteams_futures.append(EventTeamsQuery(event.key_name).fetch_async())

        live_eventteams_futures = []
        for event in live_events:
            live_eventteams_futures.append(EventTeamsQuery(event.key_name).fetch_async())

        favorite_teams = [team_future.get_result() for team_future in favorite_teams_future]

        future_events_with_teams = []
        for event, teams_future in zip(future_events, future_eventteams_futures):
            favorite_eventteams = filter(lambda t: t in favorite_teams, teams_future.get_result())
            live_teams_at_event = TeamHelper.sortTeams(favorite_eventteams)

            if live_teams_at_event:
                future_events_with_teams.append((event, live_teams_at_event))

        live_events_with_teams = EventTeamStatusHelper.buildEventTeamStatus(live_events, live_eventteams_futures, favorite_teams)

        self.template_values.update({
            'live_events_with_teams': live_events_with_teams,
            'future_events_with_teams': future_events_with_teams,
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/mytba_live.html')
        self.response.out.write(template.render(path, self.template_values))
