import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from base_controller import CacheableHandler

from models.insight import Insight

MAX_YEAR = 2013
VALID_YEARS = list(reversed(range(1992, MAX_YEAR + 1)))


class InsightsOverview(CacheableHandler):
    """
    Show Insights Overview
    """
    def __init__(self, *args, **kw):
        super(InsightsOverview, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._cache_key = "insights_overview"
        self._cache_version = 2

    def _render(self):
        template_values = {
            'valid_years': VALID_YEARS,
        }

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(0, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                template_values[insight.name] = insight

        path = os.path.join(os.path.dirname(__file__), '../templates/insights.html')
        return template.render(path, template_values)


class InsightsDetail(CacheableHandler):
    """
    Show Insights for a particular year
    """
    def __init__(self, *args, **kw):
        super(InsightsDetail, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24
        self._cache_key = "insight_detail_{}"  # (year)
        self._cache_version = 2

    def get(self, year):
        if year == '':
            return self.redirect("/insights")
        if not year.isdigit():
            self.abort(404)
        year = int(year)
        if year not in VALID_YEARS:
            self.abort(404)

        self._cache_key = self._cache_key.format(year)
        super(InsightsDetail, self).get(year)

    def _render(self, year):
        template_values = {
            'valid_years': VALID_YEARS,
            'selected_year': year,
        }

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        for insight in insights:
            if insight:
                template_values[insight.name] = insight

        path = os.path.join(os.path.dirname(__file__), '../templates/insights_details.html')
        return template.render(path, template_values)
