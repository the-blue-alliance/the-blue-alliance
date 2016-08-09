import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.model_type import ModelType
from controllers.base_controller import LoggedInHandler
from database.event_query import TeamYearEventsQuery
from database.team_query import EventTeamsQuery
from helpers.event_helper import EventHelper
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.team_helper import TeamHelper
from models.favorite import Favorite
from models.team import Team


class MyTBALiveController(LoggedInHandler):
    def get(self):
        self._require_login()
        self._require_registration()

        user = self.user_bundle.account.key
        now = datetime.datetime.now()
        team_favorites_future = Favorite.query(Favorite.model_type == ModelType.TEAM, ancestor=user).fetch_async()

        favorite_team_keys = map(lambda f: ndb.Key(Team, f.model_key), team_favorites_future.get_result())
        favorite_teams_future = ndb.get_multi_async(favorite_team_keys)

        favorite_teams = [team_future.get_result() for team_future in favorite_teams_future]

        favorite_teams_events_futures = []
        for team in favorite_teams:
            favorite_teams_events_futures.append(TeamYearEventsQuery(team.key_name, now.year).fetch_async())

        past_events_by_event = {}
        live_events_by_event = {}
        future_events_by_event = {}
        for team, events_future in zip(favorite_teams, favorite_teams_events_futures):
            events = events_future.get_result()
            if not events:
                continue
            EventHelper.sort_events(events)
            for event in events:
                if event.within_a_day:
                    if event.key_name not in live_events_by_event:
                        live_events_by_event[event.key_name] = (event, [])
                    live_events_by_event[event.key_name][1].append(team)
                elif event.start_date < now:
                    if event.key_name not in past_events_by_event:
                        past_events_by_event[event.key_name] = (event, [])
                    past_events_by_event[event.key_name][1].append(team)

            next_event = next((e for e in events if e.start_date > now and not e.within_a_day), None)
            if next_event:
                if next_event.key_name not in future_events_by_event:
                    future_events_by_event[next_event.key_name] = (next_event, [])
                future_events_by_event[next_event.key_name][1].append(team)

        past_events = []
        past_eventteams = []
        for past_event, past_eventteam in past_events_by_event.itervalues():
            past_events.append(past_event)
            past_eventteams.append(past_eventteam)
        past_events_with_teams = EventTeamStatusHelper.buildEventTeamStatus(past_events, past_eventteams, favorite_teams)
        past_events_with_teams.sort(key=lambda x: x[0].name)
        past_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        past_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        live_events = []
        live_eventteams = []
        for live_event, live_eventteam in live_events_by_event.itervalues():
            live_events.append(live_event)
            live_eventteams.append(live_eventteam)
        live_events_with_teams = EventTeamStatusHelper.buildEventTeamStatus(live_events, live_eventteams, favorite_teams)
        live_events_with_teams.sort(key=lambda x: x[0].name)

        future_events_with_teams = []
        for event_key, data in future_events_by_event.iteritems():
            future_events_with_teams.append((data[0], TeamHelper.sortTeams(data[1])))
        future_events_with_teams.sort(key=lambda x: x[0].name)
        future_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        future_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        self.template_values.update({
            'past_events_with_teams': past_events_with_teams,
            'live_events_with_teams': live_events_with_teams,
            'future_events_with_teams': future_events_with_teams,
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/mytba_live.html')
        self.response.out.write(template.render(path, self.template_values))
