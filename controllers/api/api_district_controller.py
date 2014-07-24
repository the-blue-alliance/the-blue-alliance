import json
import webapp2

from controllers.api.api_base_controller import ApiBaseController
from consts.district_type import DistrictType
from consts.event_type import EventType

from datetime import datetime

from google.appengine.ext import ndb

from helpers.district_helper import DistrictHelper
from helpers.event_helper import EventHelper
from helpers.model_to_dict import ModelToDict

from models.event import Event
from models.event_team import EventTeam
from models.team import Team

class ApiDistrictControllerBase(ApiBaseController):

    def _set_district(self, district):
        self.district_abbrev = district
        self.district = DistrictType.abbrevs[self.district_abbrev]

    @property
    def _validators(self):
        return []

class ApiDistrictListController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_list_controller_{}"  # year
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiDistrictListController, self).__init__(*args, **kw)
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.year)

    def _track_call(self, year=None):
        if year is None:
            year = datetime.now().year
        self._track_call_defer('district/list', year) 

    def _render(self, year=None):
        all_cmp_event_keys = Event.query(Event.year == int(self.year), Event.event_type_enum == EventType.DISTRICT_CMP).fetch(None, keys_only=True)    
        events = ndb.get_multi(all_cmp_event_keys)    
        district_keys = [DistrictType.type_abbrevs[event.event_district_enum] for event in events]
        return json.dumps(district_keys, ensure_ascii=True)

class ApiDistrictEventsController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_events_controller_{}_{}"  # (district_short, year)
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiDistrictEventsController, self).__init__(*args, **kw)
        self.district_abbrev = self.request.route_kwargs["district_abbrev"]
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.district_abbrev, self.year) 

    def _track_call(self, district_abbrev, year=None):
        if year is None:
            year = datetime.now().year
    
        self._track_call_defer('district/events', '{}{}'.format(year, district_abrev))

    def _render(self, district_abbrev, year=None):
        self._set_district(district_abbrev)  
        
        event_keys = Event.query(Event.year == self.year, Event.event_district_enum == self.district).fetch(None, keys_only=True)
        events = ndb.get_multi(event_keys)
        
        events = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(events, ensure_ascii=True)

class ApiDistrictRankingsController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_rankings_controller_{}_{}"  # (district_short, year)
    CACHE_VERSION = 1 
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiDistrictRankingsController, self).__init__(*args, **kw)
        self.district_abbrev = self.request.route_kwargs["district_abbrev"]
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.district_abbrev, self.year)

    def _track_call(self, district_abbrev, year=None):
        if year is None:
            year = datetime.now().year

        self._track_call_defer('district/rankings', str(year)+district_abbrev)


    def _render(self, district_abbrev, year=None):
        self._set_district(district_abbrev)

        event_keys = Event.query(Event.year == self.year, Event.event_district_enum == self.district).fetch(None, keys_only=True)
        events = ndb.get_multi(event_keys)
        
        district_cmp_keys_future = Event.query(Event.year == self.year, Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(None, keys_only=True)

        event_futures = ndb.get_multi_async(event_keys)
        event_team_keys_future = EventTeam.query(EventTeam.event.IN(event_keys)).fetch_async(None, keys_only=True)

        if self.year == 2014: # TODO: only 2014 has accurate rankings calculations
            team_futures = ndb.get_multi_async(set([ndb.Key(Team, et_key.id().split('_')[1]) for et_key in event_team_keys_future.get_result()]))

        events = [event_future.get_result() for event_future in event_futures]
        EventHelper.sort_events(events)

        district_cmp_futures = ndb.get_multi_async(district_cmp_keys_future.get_result())

        if self.year == 2014: # TODO: only 2014 has accurate rankings calculations
            team_totals = DistrictHelper.calculate_rankings(events, team_futures, self.year)
        else:
            return json.dumps([])

        rankings = []

        currentRank = 1
        for key, points in team_totals:
            point_detail = {}
            point_detail["rank"] = currentRank
            point_detail["team_key"] = key
            point_detail["event_points"] = {}
            for event in points["event_points"]:
                event_key = event[0].key_name
                point_detail["event_points"][event_key] = event[1] 
                event_details = Event.get_by_id(event_key)
                point_detail["event_points"][event[0].key_name]['district_cmp'] = True if event_details.event_type_enum == EventType.DISTRICT_CMP else False           
 
            if "rookie_bonus" in points:
                point_detail["rookie_bonus"] = points["rookie_bonus"]
            else:
                point_detail["rookie_bonus"] = 0
            point_detail["point_total"] = points["point_total"]
            rankings.append(point_detail)
            currentRank += 1
 
        return json.dumps(rankings)
            
