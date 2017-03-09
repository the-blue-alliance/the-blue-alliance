import json
import logging
import webapp2
import datetime

from google.appengine.ext import ndb

from controllers.api.api_base_controller import ApiBaseController

from database.event_query import EventListQuery

from helpers.award_helper import AwardHelper
from helpers.district_helper import DistrictHelper
from helpers.event_helper import EventHelper
from helpers.event_insights_helper import EventInsightsHelper
from helpers.model_to_dict import ModelToDict

from models.event import Event


class ApiEventController(ApiBaseController):
    CACHE_KEY_FORMAT = "apiv2_event_controller_{}"  # (event_key)
    CACHE_VERSION = 6
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiEventController, self).__init__(*args, **kw)
        self.event_key = self.request.route_kwargs["event_key"]
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    @property
    def _validators(self):
        return [("event_id_validator", self.event_key)]

    def _set_event(self, event_key):
        self.event = Event.get_by_id(event_key)
        if self.event is None:
            self._errors = json.dumps({"404": "%s event not found" % self.event_key})
            self.abort(404)

    def _track_call(self, event_key):
        self._track_call_defer('event', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        event_dict = ModelToDict.eventConverter(self.event)

        return json.dumps(event_dict, ensure_ascii=True)


class ApiEventTeamsController(ApiEventController):
    CACHE_KEY_FORMAT = "apiv2_event_teams_controller_{}"  # (event_key)
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiEventTeamsController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    def _track_call(self, event_key):
        self._track_call_defer('event/teams', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        teams = filter(None, self.event.teams)
        team_dicts = [ModelToDict.teamConverter(team) for team in teams]

        return json.dumps(team_dicts, ensure_ascii=True)


class ApiEventMatchesController(ApiEventController):
    CACHE_KEY_FORMAT = "apiv2_event_matches_controller_{}"  # (event_key)
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiEventMatchesController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    def _track_call(self, event_key):
        self._track_call_defer('event/matches', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        matches = self.event.matches
        match_dicts = [ModelToDict.matchConverter(match) for match in matches]

        return json.dumps(match_dicts, ensure_ascii=True)


class ApiEventStatsController(ApiEventController):
    CACHE_KEY_FORMAT = "apiv2_event_stats_controller_{}"  # (event_key)
    CACHE_VERSION = 5
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiEventStatsController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    def _track_call(self, event_key):
        self._track_call_defer('event/stats', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        stats = {}
        matchstats = self.event.matchstats
        if matchstats:
            for stat in ['oprs', 'dprs', 'ccwms']:
                if stat in matchstats:
                    stats[stat] = matchstats[stat]

        year_specific = EventInsightsHelper.calculate_event_insights(self.event.matches, self.event.year)
        if year_specific:
            stats['year_specific'] = year_specific

        return json.dumps(stats)


class ApiEventRankingsController(ApiEventController):
    CACHE_KEY_FORMAT = "apiv2_event_rankings_controller_{}"  # (event_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiEventRankingsController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    def _track_call(self, event_key):
        self._track_call_defer('event/rankings', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        ranks = json.dumps(Event.get_by_id(event_key).rankings)
        if ranks is None or ranks == 'null':
            return '[]'
        else:
            return ranks


class ApiEventAwardsController(ApiEventController):
    CACHE_KEY_FORMAT = "apiv2_event_awards_controller_{}"  # (event_key)
    CACHE_VERSION = 4
    CACHE_HEADER_LENGTH = 60 * 60

    def __init__(self, *args, **kw):
        super(ApiEventAwardsController, self).__init__(*args, **kw)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    def _track_call(self, event_key):
        self._track_call_defer('event/awards', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        award_dicts = [ModelToDict.awardConverter(award) for award in AwardHelper.organizeAwards(self.event.awards)]
        return json.dumps(award_dicts, ensure_ascii=True)


class ApiEventDistrictPointsController(ApiEventController):
    CACHE_KEY_FORMAT = "apiv2_event_district_points_controller_{}"  # (event_key)
    CACHE_VERSION = 1
    CACHE_HEADER_LENGTH = 61

    def __init__(self, *args, **kw):
        super(ApiEventDistrictPointsController, self).__init__(*args, **kw)
        self.partial_cache_key = self.CACHE_KEY_FORMAT.format(self.event_key)

    def _track_call(self, event_key):
        self._track_call_defer('event/district_points', event_key)

    def _render(self, event_key):
        self._set_event(event_key)

        points = DistrictHelper.calculate_event_points(self.event)
        return json.dumps(points, ensure_ascii=True)


class ApiEventWeekController(ApiBaseController):
    CACHE_KEY_FORMAT = "apiv2_live_events_controller_{}"  # (start of week timestamp [Monday])
    CACHE_VERSION = 0
    CACHE_HEADER_LENGTH = 60 * 60  # One day in seconds

    # Set a datetime variable to the most recent Monday at 0:00 UTC
    def _set_week_start(self, dt):
        if dt.weekday() != 0:
            # If we're given a datetime for a non-Monday, normalize to that
            dt = dt + datetime.timedelta(days=(-1 * dt.weekday()))
        self.date = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0)

    def __init__(self, *args, **kw):
        super(ApiEventWeekController, self).__init__(*args, **kw)
        if "time" in self.request.route_kwargs and self.request.route_kwargs["time"]:
            dt = datetime.datetime.utcfromtimestamp(int(self.request.route_kwargs["time"]))
        else:
            dt = datetime.datetime.now()
        self._set_week_start(dt)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.date.isoformat())

    @property
    def _validators(self):
        return []

    def _track_call(self, time=datetime.datetime.utcnow()):
        self._track_call_defer('live_event', '{}'.format(time))

    def _render(self, time=datetime.datetime.utcnow()):
        events = EventHelper.getWeekEvents(self.date)
        event_list = [ModelToDict.eventConverter(event) for event in events]
        return json.dumps(event_list, ensure_ascii=True)


class ApiEventListController(ApiBaseController):
    CACHE_KEY_FORMAT = "apiv2_event_list_controller_{}"  # (year)
    CACHE_VERSION = 3
    CACHE_HEADER_LENGTH = 60 * 60 * 24

    def __init__(self, *args, **kw):
        super(ApiEventListController, self).__init__(*args, **kw)
        self.year = int(self.request.route_kwargs.get("year") or datetime.datetime.now().year)
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(self.year)

    @property
    def _validators(self):
        return []

    def _track_call(self, *args, **kw):
        self._track_call_defer('event/list', self.year)

    def _render(self, year=None):
        if self.year < 1992 or self.year > datetime.datetime.now().year + 1:
            self._errors = json.dumps({"404": "No events found for %s" % self.year})
            self.abort(404)

        events = EventListQuery(self.year).fetch()

        event_list = [ModelToDict.eventConverter(event) for event in events]

        return json.dumps(event_list, ensure_ascii=True)
