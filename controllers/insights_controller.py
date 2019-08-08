import datetime
import os
import tba_config

from google.appengine.ext import ndb

from base_controller import CacheableHandler

from models.insight import Insight

from template_engine import jinja2_engine

VALID_YEARS = list(reversed(tba_config.VALID_YEARS))


class InsightsOverview(CacheableHandler):
    """
    Show Insights Overview
    """
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "insights_overview"

    def __init__(self, *args, **kw):
        super(InsightsOverview, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 4

    def _render(self):
        self.template_values.update({
            'valid_years': VALID_YEARS,
        })

        insights = ndb.get_multi([ndb.Key(Insight, Insight.renderKeyName(0, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()])
        last_updated = None
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight
                if last_updated is None:
                    last_updated = insight.updated
                else:
                    last_updated = max(last_updated, insight.updated)

        self.template_values['last_updated'] = last_updated

        return jinja2_engine.render('insights.html', self.template_values)


class InsightsDetail(CacheableHandler):
    """
    Show Insights for a particular year
    """
    CACHE_VERSION = 3
    CACHE_KEY_FORMAT = "insight_detail_{}"  # (year)

    def __init__(self, *args, **kw):
        super(InsightsDetail, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 4

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
        last_updated = None
        for insight in insights:
            if insight:
                self.template_values[insight.name] = insight
                if last_updated is None:
                    last_updated = insight.updated
                else:
                    last_updated = max(last_updated, insight.updated)

        self.template_values['year_specific_insights_template'] = 'event_partials/event_insights_{}.html'.format(year)
        self.template_values['last_updated'] = last_updated

        return jinja2_engine.render('insights_details.html', self.template_values)
