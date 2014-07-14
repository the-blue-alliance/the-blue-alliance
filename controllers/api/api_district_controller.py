import json
import webapp2
import logging

from datetime import datetime

from google.appengine.ext import ndb

from models.event import Event
from helpers.model_to_dict import ModelToDict

from controllers.api.api_base_controller import ApiBaseController
from consts.district_type import DistrictType
from consts.event_type import EventType

class ApiDistrictControllerBase(ApiBaseController):

    def _set_district(self, district):
        self.district_abbrev = district
        self.district = DistrictType.abbrevs[self.district_abbrev]

    @property
    def _validators(self):
        return []

class ApiDistrictListController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_districts_{}" #year
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiDistrictListController, self).__init__(*args, **kw)
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.year)

    def _track_call(self, year=None):
        pass

    def _render(self, year=None):
        all_cmp_event_keys = Event.query(Event.year == int(self.year), Event.event_type_enum == EventType.DISTRICT_CMP).fetch(None, keys_only=True)    
        events = ndb.get_multi(all_cmp_event_keys)    
        logging.info(len(events))
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
        pass 
        #api_label = district
        #if year is not None:
        #    api_label += '/{}'.format(year)
        #self._track_call_defer('district/events', api_label)

    def _render(self, district_abbrev, year=None):
        self._set_district(district_abbrev)  
        
        event_keys = Event.query(Event.year == int(year), Event.event_district_enum == self.district).fetch(None, keys_only=True)
        events = ndb.get_multi(event_keys)
        
        events = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(events, ensure_ascii=True)

class ApiDistrictRankingsController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_rankings_controller_{}_{}"  # (district_short, year)
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiDistrictRankingsController, self).__init__(*args, **kw)
        self.district_abbrev = self.request.route_kwargs["district_abbrev"]
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.district_abbrev, self.year)

    def _track_call(self, district_abbrev, year=None):
        pass
        #api_label = district
        #if year is not None:
        #    api_label += '/{}'.format(year)
        #self._track_call_defer('district/events', api_label)

    def _render(self, district_abbrev, year=None):
        pass
