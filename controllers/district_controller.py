import datetime
import heapq
import logging
import os

from collections import defaultdict

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import CacheableHandler

from consts.district_type import DistrictType
from consts.event_type import EventType

from helpers.event_helper import EventHelper

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class DistrictList(CacheableHandler):
    """
    List all Districts.
    """
    MAX_YEAR = 2014
    VALID_YEARS = list(reversed(range(2009, MAX_YEAR + 1)))
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "district_list_{}_{}"  # (year, explicit_year)

    def __init__(self, *args, **kw):
        super(DistrictList, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def get(self, year=None, explicit_year=False):
        if year == '':
            return self.redirect("/districts")

        if year:
            if not year.isdigit():
                self.abort(404)
            year = int(year)
            if year not in self.VALID_YEARS:
                self.abort(404)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year, explicit_year)
        super(DistrictList, self).get(year, explicit_year)

    def _render(self, year=None, explicit_year=False):
        event_keys = Event.query(Event.year == year, Event.event_type_enum.IN({EventType.DISTRICT, EventType.DISTRICT_CMP})).fetch(None, keys_only=True)
        events = ndb.get_multi(event_keys)
        EventHelper.sort_events(events)

        district_type_enums = set()
        for event in events:
            district_type_enums.add(event.event_district_enum)

        events_by_district = defaultdict(list)
        for event in events:
            if event.event_district_enum is None:
                logging.warning("District event {} has unknown district type!".format(event.key.id()))
            else:
                district = (DistrictType.type_names[event.event_district_enum], DistrictType.type_abbrevs[event.event_district_enum])
                events_by_district[district].append(event)

        districts_and_events = []
        for district in sorted(events_by_district.keys(), key=lambda d: d[0]):
            districts_and_events.append((district, events_by_district[district]))

        template_values = {
            'explicit_year': explicit_year,
            'selected_year': year,
            'valid_years': self.VALID_YEARS,
            'districts_and_events': districts_and_events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/district_list.html')
        return template.render(path, template_values)


class DistrictRankings(CacheableHandler):
    CACHE_KEY_FORMAT = "district_rankings_{}_{}"  # (district_abbrev, year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(DistrictRankings, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def get(self, year, district_abbrev):
        if district_abbrev not in DistrictType.abbrevs.keys():
            self.abort(404)

        self._cache_key = self.CACHE_KEY_FORMAT.format(district_abbrev, year)
        super(DistrictRankings, self).get(district_abbrev, year)

    def _render(self, district_abbrev, year):
        district_type = DistrictType.abbrevs[district_abbrev]
        year = int(year)

        event_keys = Event.query(Event.year == year, Event.event_district_enum == district_type).fetch(None, keys_only=True)
        if not event_keys:
            self.abort(404)

        all_event_keys_future = Event.query(Event.event_district_enum == district_type).fetch_async(None, keys_only=True)

        district_cmp_keys_future = Event.query(Event.year == year, Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(None, keys_only=True)  # to compute valid_districts

        event_futures = ndb.get_multi_async(event_keys)
        event_team_keys_future = EventTeam.query(EventTeam.event.IN(event_keys)).fetch_async(None, keys_only=True)
        team_futures = ndb.get_multi_async(set([ndb.Key(Team, et_key.id().split('_')[1]) for et_key in event_team_keys_future.get_result()]))

        events = [event_future.get_result() for event_future in event_futures]
        EventHelper.sort_events(events)

        district_cmp_futures = ndb.get_multi_async(district_cmp_keys_future.get_result())

        # aggregate points from first two events and district championship
        team_attendance_count = defaultdict(int)
        team_totals = defaultdict(lambda: {
            'event_points': [],
            'point_total': 0,
            'tiebreakers': 5 * [0] + [[]],  # there are 6 different tiebreakers
        })
        for event in events:
            if event.event_type_enum == EventType.DISTRICT_CMP:
                continue
            if event.district_points is not None:
                for team_key in event.district_points['points'].keys():
                    team_attendance_count[team_key] += 1
                    if team_attendance_count[team_key] <= 2 or event.event_type_enum == EventType.DISTRICT_CMP:
                        team_totals[team_key]['event_points'].append((event, event.district_points['points'][team_key]))
                        team_totals[team_key]['point_total'] += event.district_points['points'][team_key]['total']

                        # add tiebreakers in order
                        team_totals[team_key]['tiebreakers'][0] += event.district_points['points'][team_key]['elim_points']
                        team_totals[team_key]['tiebreakers'][1] = max(event.district_points['points'][team_key]['elim_points'], team_totals[team_key]['tiebreakers'][1])
                        team_totals[team_key]['tiebreakers'][2] += event.district_points['points'][team_key]['alliance_points']
                        team_totals[team_key]['tiebreakers'][3] = max(event.district_points['points'][team_key]['qual_points'], team_totals[team_key]['tiebreakers'][3])
                        team_totals[team_key]['tiebreakers'][4] += event.district_points['tiebreakers'][team_key]['qual_wins']
                        team_totals[team_key]['tiebreakers'][5] = heapq.nlargest(3, event.district_points['tiebreakers'][team_key]['highest_qual_scores'] + team_totals[team_key]['tiebreakers'][5])

        # adding in rookie bonus
        for team_future in team_futures:
            team = team_future.get_result()
            bonus = None
            if team.rookie_year == year:
                bonus = 10
            elif team.rookie_year == year - 1:
                bonus = 5
            if bonus is not None:
                team_totals[team.key.id()]['rookie_bonus'] = bonus
                team_totals[team.key.id()]['point_total'] += bonus

        team_totals = sorted(team_totals.items(),
            key=lambda (_, totals): [
                -totals['point_total'],
                -totals['tiebreakers'][0],
                -totals['tiebreakers'][1],
                -totals['tiebreakers'][2],
                -totals['tiebreakers'][3],
                -totals['tiebreakers'][4]] + [-score for score in totals['tiebreakers'][5]]
            )

        valid_districts = set()
        for district_cmp_future in district_cmp_futures:
            district_cmp = district_cmp_future.get_result()
            cmp_dis_type = district_cmp.event_district_enum
            if cmp_dis_type is None:
                logging.warning("District event {} has unknown district type!".format(district_cmp.key.id()))
            else:
                valid_districts.add((DistrictType.type_names[cmp_dis_type], DistrictType.type_abbrevs[cmp_dis_type]))
        valid_districts = sorted(valid_districts, key=lambda (name, _): name)

        template_values = {
            'year': year,
            'valid_years': sorted(set([int(event_key.id()[:4]) for event_key in all_event_keys_future.get_result()])),
            'valid_districts': valid_districts,
            'district_name': DistrictType.type_names[district_type],
            'district_abbrev': district_abbrev,
            'team_totals': team_totals,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/district_rankings.html')
        return template.render(path, template_values)
