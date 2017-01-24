import json
import webapp2

from controllers.api.api_base_controller import ApiBaseController
from consts.district_type import DistrictType
from consts.event_type import EventType

from datetime import datetime

from database.district_query import DistrictsInYearQuery
from database.event_query import DistrictEventsQuery
from google.appengine.ext import ndb

from database.team_query import DistrictTeamsQuery
from helpers.district_helper import DistrictHelper
from helpers.event_helper import EventHelper
from helpers.model_to_dict import ModelToDict
from models import team
from models.district import District
from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class ApiDistrictControllerBase(ApiBaseController):

    def _set_district(self, district, year):
        self.district_abbrev = district
        self.year = year

    @property
    def _validators(self):
        return [("district_id_validator", "{}{}".format(self.year, self.district_abbrev))]


class ApiDistrictListController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_list_controller_{}"  # year
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiDistrictListController, self).__init__(*args, **kw)
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.year)

    @property
    def _validators(self):
        '''
        No validators for this endpoint
        '''
        return []

    def _track_call(self, year=None):
        if year is None:
            year = datetime.now().year
        self._track_call_defer('district/list', year)

    def _render(self, year=None):
        all_districts = DistrictsInYearQuery(self.year).fetch()
        districts = list()
        for district in all_districts:
            dictionary = dict()
            dictionary["key"] = district.abbreviation
            dictionary["name"] = district.display_name
            districts.append(dictionary)

        return json.dumps(districts, ensure_ascii=True)


class ApiDistrictEventsController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_events_controller_{}_{}"  # (district_short, year)
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiDistrictEventsController, self).__init__(*args, **kw)
        self.district_abbrev = self.request.route_kwargs["district_abbrev"]
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.district_abbrev, self.year)

    def _track_call(self, district_abbrev, year=None):
        if year is None:
            year = datetime.now().year

        self._track_call_defer('district/events', '{}{}'.format(year, district_abbrev))

    def _render(self, district_abbrev, year=None):
        self._set_district(district_abbrev, self.year)

        events = DistrictEventsQuery('{}{}'.format(self.year, self.district_abbrev)).fetch()

        events = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(events, ensure_ascii=True)


class ApiDistrictRankingsController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_rankings_controller_{}_{}"  # (district_short, year)
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiDistrictRankingsController, self).__init__(*args, **kw)
        self.district_abbrev = self.request.route_kwargs["district_abbrev"]
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.district_abbrev, self.year)

    def _track_call(self, district_abbrev, year=None):
        if year is None:
            year = datetime.now().year

        self._track_call_defer('district/rankings', '{}{}'.format(year, district_abbrev))

    def _render(self, district_abbrev, year=None):
        self._set_district(district_abbrev, self.year)

        if self.year < 2009:
            return json.dumps([], ensure_ascii=True)

        events_future = DistrictEventsQuery(District.renderKeyName(self.year, district_abbrev)).fetch_async()
        district_teams_future = DistrictTeamsQuery("{}{}".format(year, district_abbrev)).fetch_async()

        events = events_future.get_result()
        if not events:
            return json.dumps([], ensure_ascii=True)
        EventHelper.sort_events(events)

        team_totals = DistrictHelper.calculate_rankings(events, district_teams_future.get_result(), self.year)

        rankings = []

        current_rank = 1
        for key, points in team_totals:
            point_detail = {}
            point_detail["rank"] = current_rank
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
            current_rank += 1

        return json.dumps(rankings)


class ApiDistrictTeamsController(ApiDistrictControllerBase):
    CACHE_KEY_FORMAT = "apiv2_district_teams_controller_{}_{}"  # (district_short, year)
    CACHE_VERSION = 2
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiDistrictTeamsController, self).__init__(*args, **kw)
        self.district_abbrev = self.request.route_kwargs["district_abbrev"]
        self.year = int(self.request.route_kwargs["year"] or datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.district_abbrev, self.year)

    def _track_call(self, district_abbrev, year=None):
        if year is None:
            year = datetime.now().year

        self._track_call_defer('district/teams', '{}{}'.format(year, district_abbrev))

    def _render(self, district_abbrev, year=None):
        self._set_district(district_abbrev, self.year)

        district_teams = DistrictTeamsQuery('{}{}'.format(self.year, self.district_abbrev)).fetch()

        district_teams_dict = [ModelToDict.teamConverter(team) for team in district_teams]

        return json.dumps(district_teams_dict, ensure_ascii=True)
