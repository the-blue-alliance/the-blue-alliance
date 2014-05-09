import datetime
import os

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler

from consts.district_type import DistrictType

from renderers.rankings_renderer import RankingsRenderer


class RankingsCanonical(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(RankingsCanonical, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "rankings_canonical"
        self._cache_version = 1

    def _render(self):
        year = datetime.datetime.now().year

        rendered_result = RankingsRenderer.render_rankings_details(self, year, True)
        if rendered_result is None:
            self.abort(404)
        else:
            return rendered_result


class RankingsDetail(CacheableHandler):
    LONG_CACHE_EXPIRATION = 60 * 60 * 24
    SHORT_CACHE_EXPIRATION = 60 * 5

    def __init__(self, *args, **kw):
        super(RankingsDetail, self).__init__(*args, **kw)
        self._cache_expiration = self.LONG_CACHE_EXPIRATION
        self._cache_key = "rankings_detail_{}_{}"  # (year, district_abbrev)
        self._cache_version = 1

    def get(self, year, district_abbrev):
        if district_abbrev not in DistrictType.abbrevs.keys():
            self.abort(404)
        if int(year) not in RankingsRenderer.VALID_YEARS:
            self.abort(404)

        self._cache_key = self._cache_key.format(year, district_abbrev)
        super(RankingsDetail, self).get(year, district_abbrev)

    def _render(self, year, district_abbrev):
        rendered_result = RankingsRenderer.render_rankings_details(self, district_abbrev, int(year), False)
        if rendered_result is None:
            self.abort(404)
        else:
            return rendered_result
