import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler

from models.insight import Insight

MAX_YEAR = 2015
VALID_YEARS = list(reversed(range(1992, MAX_YEAR + 1)))


class InsightsOverview(CacheableHandler):
    """
    Show Insights Overview
    """
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "insights_overview"

    def __init__(self, *args, **kw):
        super(InsightsOverview, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _render(self):
        self.template_values.update({
            'valid_years': VALID_YEARS,
        })

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(0, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight

        path = os.path.join(os.path.dirname(__file__), '../templates/insights.html')
        return template.render(path, self.template_values)


class InsightsDetail(CacheableHandler):
    """
    Show Insights for a particular year
    """
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "insight_detail_{}"  # (year)

    def __init__(self, *args, **kw):
        super(InsightsDetail, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def get(self, year):
        if year == '':
            return self.redirect("/insights")
        if not year.isdigit():
            self.abort(404)
        year = int(year)
        if year not in VALID_YEARS:
            self.abort(404)

        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year)
        super(InsightsDetail, self).get(year)

    def _render(self, year):
        self.template_values.update({
            'valid_years': VALID_YEARS,
            'selected_year': year,
        })

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight

        path = os.path.join(os.path.dirname(__file__), '../templates/insights_details.html')
        return template.render(path, self.template_values)
