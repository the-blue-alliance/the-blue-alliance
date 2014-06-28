import datetime
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import CacheableHandler

from consts.district_type import DistrictType
from consts.event_type import EventType

from helpers.district_helper import DistrictHelper
from helpers.event_helper import EventHelper

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class DistrictDetail(CacheableHandler):
    CACHE_KEY_FORMAT = "district_detail_{}_{}_{}"  # (district_abbrev, year, explicit_year)
    CACHE_VERSION = 0

    def __init__(self, *args, **kw):
        super(DistrictDetail, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

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

        self._cache_key = self.CACHE_KEY_FORMAT.format(district_abbrev, year, explicit_year)
        super(DistrictDetail, self).get(district_abbrev, year, explicit_year)

    def _render(self, district_abbrev, year=None, explicit_year=False):
        district_type = DistrictType.abbrevs[district_abbrev]

        event_keys = Event.query(Event.year == year, Event.event_district_enum == district_type).fetch(None, keys_only=True)
        if not event_keys:
            self.abort(404)

        # needed for valid_years
        all_cmp_event_keys_future = Event.query(Event.event_district_enum == district_type, Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(None, keys_only=True)

        # needed for valid_districts
        district_cmp_keys_future = Event.query(Event.year == year, Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(None, keys_only=True)  # to compute valid_districts

        event_futures = ndb.get_multi_async(event_keys)
        event_team_keys_future = EventTeam.query(EventTeam.event.IN(event_keys)).fetch_async(None, keys_only=True)
        if year == 2014:  # TODO: only 2014 has accurate rankings calculations
            team_futures = ndb.get_multi_async(set([ndb.Key(Team, et_key.id().split('_')[1]) for et_key in event_team_keys_future.get_result()]))

        events = [event_future.get_result() for event_future in event_futures]
        EventHelper.sort_events(events)

        district_cmp_futures = ndb.get_multi_async(district_cmp_keys_future.get_result())

        if year == 2014:  # TODO: only 2014 has accurate rankings calculations
            team_totals = DistrictHelper.calculate_rankings(events, team_futures, year)
        else:
            team_totals = None

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
            'explicit_year': explicit_year,
            'year': year,
            'valid_years': sorted(set([int(event_key.id()[:4]) for event_key in all_cmp_event_keys_future.get_result()])),
            'valid_districts': valid_districts,
            'district_name': DistrictType.type_names[district_type],
            'district_abbrev': district_abbrev,
            'events': events,
            'team_totals': team_totals,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/district_details.html')
        return template.render(path, template_values)
