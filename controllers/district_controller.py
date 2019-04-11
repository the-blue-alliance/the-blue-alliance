import datetime
import logging
import os

from google.appengine.ext import ndb

from controllers.base_controller import CacheableHandler

from consts.district_type import DistrictType
from consts.event_type import EventType
from database.district_query import DistrictQuery, DistrictHistoryQuery, DistrictsInYearQuery
from database.event_query import DistrictEventsQuery
from database.team_query import DistrictTeamsQuery, EventTeamsQuery
from helpers.event_helper import EventHelper
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.team_helper import TeamHelper

from models.event import Event
from models.event_team import EventTeam
from models.team import Team

from template_engine import jinja2_engine


class DistrictDetail(CacheableHandler):
    CACHE_KEY_FORMAT = "district_detail_{}_{}_{}"  # (district_abbrev, year, explicit_year)
    CACHE_VERSION = 2

    def __init__(self, *args, **kw):
        super(DistrictDetail, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 15

    def get(self, district_abbrev, year=None, explicit_year=False):
        if year == '':
            return self.redirect("/")

        if year:
            if not year.isdigit():
                self.abort(404)
            year = int(year)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(district_abbrev, year, explicit_year)
        super(DistrictDetail, self).get(district_abbrev, year, explicit_year)

    def _render(self, district_abbrev, year=None, explicit_year=False):
        district = DistrictQuery('{}{}'.format(year, district_abbrev)).fetch()
        if not district:
            self.abort(404)

        events_future = DistrictEventsQuery(district.key_name).fetch_async()

        # needed for district teams
        district_teams_future = DistrictTeamsQuery(district.key_name).fetch_async()

        # needed for valid_years
        history_future = DistrictHistoryQuery(district.abbreviation).fetch_async()

        # needed for valid_districts
        districts_in_year_future = DistrictsInYearQuery(district.year).fetch_async()

        # needed for active team statuses
        live_events = []
        if year == datetime.datetime.now().year:  # Only show active teams for current year
            live_events = EventHelper.getWeekEvents()
        live_eventteams_futures = []
        for event in live_events:
            live_eventteams_futures.append(EventTeamsQuery(event.key_name).fetch_async())

        events = events_future.get_result()
        EventHelper.sort_events(events)
        events_by_key = {}
        for event in events:
            events_by_key[event.key.id()] = event
        week_events = EventHelper.groupByWeek(events)

        valid_districts = set()
        districts_in_year = districts_in_year_future.get_result()
        for dist in districts_in_year:
            valid_districts.add((dist.display_name, dist.abbreviation))
        valid_districts = sorted(valid_districts, key=lambda (name, _): name)

        teams = TeamHelper.sortTeams(district_teams_future.get_result())
        team_keys = set([t.key.id() for t in teams])

        num_teams = len(teams)
        middle_value = num_teams / 2
        if num_teams % 2 != 0:
            middle_value += 1
        teams_a, teams_b = teams[:middle_value], teams[middle_value:]

        # Currently Competing Team Status
        event_team_keys = []
        for event, teams_future in zip(live_events, live_eventteams_futures):
            for team in teams_future.get_result():
                if team.key.id() in team_keys:
                    event_team_keys.append(ndb.Key(EventTeam, '{}_{}'.format(event.key.id(), team.key.id())))  # Should be in context cache

        ndb.get_multi(event_team_keys)  # Warms context cache
        live_events_with_teams = []
        for event, teams_future in zip(live_events, live_eventteams_futures):
            teams_and_statuses = []
            has_teams = False
            for team in teams_future.get_result():
                if team.key.id() in team_keys:
                    has_teams = True
                    event_team = EventTeam.get_by_id('{}_{}'.format(event.key.id(), team.key.id()))  # Should be in context cache
                    if event_team is None:
                        logging.info("No EventTeam for {}_{}".format(event.key.id(), team.key.id()))
                        continue
                    status_str = {
                        'alliance': EventTeamStatusHelper.generate_team_at_event_alliance_status_string(team.key.id(), event_team.status),
                        'playoff': EventTeamStatusHelper.generate_team_at_event_playoff_status_string(team.key.id(), event_team.status),
                    }
                    teams_and_statuses.append((
                        team,
                        event_team.status,
                        status_str
                    ))
            if has_teams:
                teams_and_statuses.sort(key=lambda x: x[0].team_number)
                live_events_with_teams.append((event, teams_and_statuses))
        live_events_with_teams.sort(key=lambda x: x[0].name)
        live_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoStartDate(x[0]))
        live_events_with_teams.sort(key=lambda x: EventHelper.distantFutureIfNoEndDate(x[0]))

        # Get valid years
        district_history = history_future.get_result()
        valid_years = map(lambda d: d.year, district_history)
        valid_years = sorted(valid_years)

        self.template_values.update({
            'explicit_year': explicit_year,
            'year': year,
            'valid_years': valid_years,
            'valid_districts': valid_districts,
            'district_name': district.display_name,
            'district_abbrev': district_abbrev,
            'week_events': week_events,
            'events_by_key': events_by_key,
            'rankings': district.rankings,
            'advancement': district.advancement,
            'teams_a': teams_a,
            'teams_b': teams_b,
            'live_events_with_teams': live_events_with_teams,
        })

        return jinja2_engine.render('district_details.html', self.template_values)
