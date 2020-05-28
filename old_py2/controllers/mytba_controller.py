from collections import defaultdict
import datetime
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.model_type import ModelType
from controllers.base_controller import LoggedInHandler
from database.award_query import TeamYearAwardsQuery
from database.event_query import TeamYearEventsQuery
from helpers.award_helper import AwardHelper
from helpers.event_helper import EventHelper
from helpers.event_team_status_helper import EventTeamStatusHelper
from models.event_team import EventTeam
from models.favorite import Favorite
from models.team import Team


class MyTBALiveController(LoggedInHandler):
    def get(self):
        self._require_registration()

        user = self.user_bundle.account.key
        now = datetime.datetime.now()

        year = self.request.get('year')
        if year and year.isdigit():
            year = int(year)
        else:
            year = now.year

        team_favorites_future = Favorite.query(Favorite.model_type == ModelType.TEAM, ancestor=user).fetch_async()

        favorite_team_keys = map(lambda f: ndb.Key(Team, f.model_key), team_favorites_future.get_result())
        favorite_teams_future = ndb.get_multi_async(favorite_team_keys)

        favorite_teams = [team_future.get_result() for team_future in favorite_teams_future]

        favorite_teams_events_futures = []
        favorite_teams_awards_futures = {}
        for team in favorite_teams:
            favorite_teams_events_futures.append(TeamYearEventsQuery(team.key_name, year).fetch_async())
            favorite_teams_awards_futures[team.key.id()] = TeamYearAwardsQuery(team.key_name, year).fetch_async()

        past_events_by_event = {}
        live_events_by_event = {}
        future_events_by_event = {}
        favorite_event_team_keys = []
        for team, events_future in zip(favorite_teams, favorite_teams_events_futures):
            events = events_future.get_result()
            if not events:
                continue
            EventHelper.sort_events(events)  # Sort by date
            for event in events:
                favorite_event_team_keys.append(ndb.Key(EventTeam, '{}_{}'.format(event.key.id(), team.key.id())))
                if event.within_a_day:
                    if event.key_name not in live_events_by_event:
                        live_events_by_event[event.key_name] = (event, [])
                    live_events_by_event[event.key_name][1].append(team)
                elif event.start_date < now:
                    if event.key_name not in past_events_by_event:
                        past_events_by_event[event.key_name] = (event, [])
                    past_events_by_event[event.key_name][1].append(team)
                else:
                    if event.key_name not in future_events_by_event:
                        future_events_by_event[event.key_name] = (event, [])
                    future_events_by_event[event.key_name][1].append(team)

        event_team_awards = defaultdict(lambda: defaultdict(list))
        for team_key, awards_future in favorite_teams_awards_futures.items():
            for award in awards_future.get_result():
                event_team_awards[award.event.id()][team_key].append(award)

        ndb.get_multi(favorite_event_team_keys)  # Warms context cache

        past_events_with_teams = []
        for event, teams in past_events_by_event.itervalues():
            teams_and_statuses = []
            for team in teams:
                event_team = EventTeam.get_by_id('{}_{}'.format(event.key.id(), team.key.id()))  # Should be in context cache
                status_str = {
                    'alliance': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team.key.id(), event_team.status),
                    'playoff': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team.key.id(), event_team.status),
                }
                teams_and_statuses.append((
                    team,
                    event_team.status,
                    status_str,
                    AwardHelper.organizeAwards(event_team_awards[event.key.id()][team.key.id()])
                ))
            teams_and_statuses.sort(key=lambda x: x[0].team_number)
            past_events_with_teams.append((event, teams_and_statuses))
        past_events_with_teams.sort(key=lambda x: x[0].name)
        past_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        past_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        live_events_with_teams = []
        for event, teams in live_events_by_event.itervalues():
            teams_and_statuses = []
            for team in teams:
                event_team = EventTeam.get_by_id('{}_{}'.format(event.key.id(), team.key.id()))  # Should be in context cache
                status_str = {
                    'alliance': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team.key.id(), event_team.status),
                    'playoff': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team.key.id(), event_team.status),
                }
                teams_and_statuses.append((
                    team,
                    event_team.status,
                    status_str
                ))
            teams_and_statuses.sort(key=lambda x: x[0].team_number)
            live_events_with_teams.append((event, teams_and_statuses))
        live_events_with_teams.sort(key=lambda x: x[0].name)
        live_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        live_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        future_events_with_teams = []
        for event, teams in future_events_by_event.itervalues():
            teams.sort(key=lambda t: t.team_number)
            future_events_with_teams.append((event, teams))
        future_events_with_teams.sort(key=lambda x: x[0].name)
        future_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        future_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        self.template_values.update({
            'year': year,
            'past_only': year < now.year,
            'past_events_with_teams': past_events_with_teams,
            'live_events_with_teams': live_events_with_teams,
            'future_events_with_teams': future_events_with_teams,
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/mytba_live.html')
        self.response.out.write(template.render(path, self.template_values))
