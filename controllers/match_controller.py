import json
import os

from base_controller import CacheableHandler
from database.gdcv_data_query import MatchGdcvDataQuery
from models.event import Event
from models.match import Match
from models.zebra_motionworks import ZebraMotionWorks
from template_engine import jinja2_engine


class MatchDetail(CacheableHandler):
    """
    Display a Match.
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 61
    CACHE_VERSION = 4
    CACHE_KEY_FORMAT = "match_detail_{}"  # (match_key)
    VALID_BREAKDOWN_YEARS = set([2015, 2016, 2017, 2018, 2019, 2020])

    def __init__(self, *args, **kw):
        super(MatchDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, match_key):
        if not match_key:
            return self.redirect("/")

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(match_key)
        super(MatchDetail, self).get(match_key)

    def _render(self, match_key):
        try:
            match_future = Match.get_by_id_async(match_key)
            event_future = Event.get_by_id_async(match_key.split("_")[0])
            match = match_future.get_result()
            event = event_future.get_result()
        except Exception, e:
            self.abort(404)

        if not match:
            self.abort(404)

        zebra_data = ZebraMotionWorks.get_by_id(match_key)
        gdcv_data = MatchGdcvDataQuery(match_key).fetch()
        timeseries_data = None
        if gdcv_data and len(gdcv_data) >= 147 and len(gdcv_data) <= 150:  # Santiy checks on data
            timeseries_data = json.dumps(gdcv_data)

        match_breakdown_template = None
        if match.score_breakdown is not None and match.year in self.VALID_BREAKDOWN_YEARS:
            match_breakdown_template = 'match_partials/match_breakdown/match_breakdown_{}.html'.format(match.year)

        self.template_values.update({
            "event": event,
            "match": match,
            "match_breakdown_template": match_breakdown_template,
            "timeseries_data": timeseries_data,
            "zebra_data": json.dumps(zebra_data.data) if zebra_data else None,
        })

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('match_details.html', self.template_values)


class MatchTimeseries(CacheableHandler):
    """
    Display a Match timeseries chart.
    """
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 61
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "match_timeseries_{}"  # (match_key)

    def __init__(self, *args, **kw):
        super(MatchTimeseries, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION

    def get(self, match_key):
        if not match_key:
            return self.redirect("/")

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(match_key)
        super(MatchTimeseries, self).get(match_key)

    def _render(self, match_key):
        try:
            match_future = Match.get_by_id_async(match_key)
            event_future = Event.get_by_id_async(match_key.split("_")[0])
            match = match_future.get_result()
            event = event_future.get_result()
        except Exception, e:
            self.abort(404)

        if not match:
            self.abort(404)

        gdcv_data = MatchGdcvDataQuery(match_key).fetch()
        timeseries_data = None
        if gdcv_data and len(gdcv_data) >= 147 and len(gdcv_data) <= 150:  # Santiy checks on data
            timeseries_data = json.dumps(gdcv_data)

        self.template_values.update({
            "event": event,
            "match": match,
            "timeseries_data": timeseries_data,
        })

        if event.within_a_day:
            self._cache_expiration = self.SHORT_CACHE_EXPIRATION

        return jinja2_engine.render('match_timeseries.html', self.template_values)
