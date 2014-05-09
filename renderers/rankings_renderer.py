import logging
import os

from collections import defaultdict

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.district_type import DistrictType
from consts.event_type import EventType

from helpers.event_helper import EventHelper

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class RankingsRenderer(object):
    MAX_YEAR = 2014
    VALID_YEARS = list(reversed(range(2013, MAX_YEAR + 1)))

    @classmethod
    def render_rankings_details(cls, handler, district_abbrev, year, is_canonical):
        district_type = DistrictType.abbrevs[district_abbrev]

        event_keys = Event.query(Event.year == year, Event.event_district_enum == district_type).fetch(None, keys_only=True)
        if not event_keys:
            return None

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
        })
        for event in events:
            if event.district_points is not None:
                for team_key in event.district_points['points'].keys():
                    team_attendance_count[team_key] += 1
                    if team_attendance_count[team_key] <= 2 or event.event_type_enum == EventType.DISTRICT_CMP:
                        team_totals[team_key]['event_points'].append((event, event.district_points['points'][team_key]))
                        team_totals[team_key]['point_total'] += event.district_points['points'][team_key]['total']

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

        team_totals = sorted(team_totals.items(), key=lambda (_, totals): -totals['point_total'])

        valid_districts = set()
        for district_cmp_future in district_cmp_futures:
            district_cmp = district_cmp_future.get_result()
            cmp_dis_type = district_cmp.event_district_enum
            valid_districts.add((DistrictType.type_names[cmp_dis_type], DistrictType.type_abbrevs[cmp_dis_type]))
        valid_districts = sorted(valid_districts, key=lambda (name, _): name)

        template_values = {
            'is_canonical': is_canonical,
            'year': year,
            'valid_years':  cls.VALID_YEARS,
            'valid_districts': valid_districts,
            'district_name': DistrictType.type_names[district_type],
            'team_totals': team_totals,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/rankings_details.html')
        return template.render(path, template_values)
