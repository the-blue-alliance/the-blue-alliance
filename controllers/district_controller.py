import datetime
import logging
import os

from google.appengine.ext import ndb

from controllers.base_controller import CacheableHandler

from consts.district_type import DistrictType
from consts.event_type import EventType

from database.team_query import DistrictTeamsQuery, EventTeamsQuery
from helpers.district_helper import DistrictHelper
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

        if district_abbrev not in DistrictType.abbrevs.keys():
            self.abort(404)

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(district_abbrev, year, explicit_year)
        super(DistrictDetail, self).get(district_abbrev, year, explicit_year)

    def _render(self, district_abbrev, year=None, explicit_year=False):
        district_type = DistrictType.abbrevs[district_abbrev]

        event_keys = Event.query(Event.year == year, Event.event_district_enum == district_type).fetch(None, keys_only=True)
        if not event_keys:
            self.abort(404)

        # needed for district teams
        district_key = '{}{}'.format(year, district_abbrev)
        district_teams_future = DistrictTeamsQuery(district_key).fetch_async()

        # needed for valid_years
        all_cmp_event_keys_future = Event.query(Event.event_district_enum == district_type, Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(None, keys_only=True)

        # needed for valid_districts
        district_cmp_keys_future = Event.query(Event.year == year, Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(None, keys_only=True)  # to compute valid_districts

        # Needed for active team statuses
        live_events = []
        if year == datetime.datetime.now().year:  # Only show active teams for current year
            live_events = EventHelper.getWeekEvents()
        live_eventteams_futures = []
        for event in live_events:
            live_eventteams_futures.append(EventTeamsQuery(event.key_name).fetch_async())

        event_futures = ndb.get_multi_async(event_keys)
        event_team_keys_future = EventTeam.query(EventTeam.event.IN(event_keys)).fetch_async(None, keys_only=True)
        team_futures = ndb.get_multi_async(set([ndb.Key(Team, et_key.id().split('_')[1]) for et_key in event_team_keys_future.get_result()]))

        events = [event_future.get_result() for event_future in event_futures]
        EventHelper.sort_events(events)
        week_events = EventHelper.groupByWeek(events)

        district_cmp_futures = ndb.get_multi_async(district_cmp_keys_future.get_result())

        team_totals = DistrictHelper.calculate_rankings(events, team_futures, year)

        valid_districts = set()
        for district_cmp_future in district_cmp_futures:
            district_cmp = district_cmp_future.get_result()
            cmp_dis_type = district_cmp.event_district_enum
            if cmp_dis_type is None:
                logging.warning("District event {} has unknown district type!".format(district_cmp.key.id()))
            else:
                valid_districts.add((DistrictType.type_names[cmp_dis_type], DistrictType.type_abbrevs[cmp_dis_type]))
        valid_districts = sorted(valid_districts, key=lambda (name, _): name)

        teams = TeamHelper.sortTeams(district_teams_future.get_result())

        num_teams = len(teams)
        middle_value = num_teams / 2
        if num_teams % 2 != 0:
            middle_value += 1
        teams_a, teams_b = teams[:middle_value], teams[middle_value:]

        # Currently Competing Team Status
        live_events_with_teams = EventTeamStatusHelper.buildEventTeamStatus(live_events, live_eventteams_futures, teams)
        live_events_with_teams.sort(key=lambda x: x[0].name)

        self.template_values.update({
            'explicit_year': explicit_year,
            'year': year,
            'valid_years': sorted(set([int(event_key.id()[:4]) for event_key in all_cmp_event_keys_future.get_result()])),
            'valid_districts': valid_districts,
            'district_name': DistrictType.type_names[district_type],
            'district_abbrev': district_abbrev,
            'week_events': week_events,
            'team_totals': team_totals,
            'teams_a': teams_a,
            'teams_b': teams_b,
            'live_events_with_teams': live_events_with_teams,
        })

        return jinja2_engine.render('district_details.html', self.template_values)
