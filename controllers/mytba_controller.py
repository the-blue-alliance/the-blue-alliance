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
from helpers.mytba_helper import MyTBAHelper
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

        favorite_teams, favorite_teams_events_futures, favorite_teams_awards_futures = \
            MyTBAHelper.build_live_favorite_futures(user, year)

        past_events_by_event, live_events_by_event, future_events_by_event, favorite_event_team_keys, event_team_awards = \
            MyTBAHelper.render_favorite_teams_events(favorite_teams,
                                                     favorite_teams_events_futures,
                                                     favorite_teams_awards_futures)

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

        live_events_with_teams = MyTBAHelper.render_live_events_with_teams(live_events_by_event)

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
