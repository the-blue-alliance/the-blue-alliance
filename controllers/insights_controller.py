import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler

from models.insight import Insight

VALID_YEARS = [2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004, 2003, 2002]

class InsightsOverview(BaseHandler):
    """
    Show Insights Overview
    """
    def get(self):
        memcache_key = "insights_overview"
        html = memcache.get(memcache_key)
        
        if html is None:
            template_values = {
                'valid_years': VALID_YEARS,
            }
            
            insight_futures = [Insight.get_by_id_async(Insight.renderKeyName(None, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()]
            for insight_future in insight_futures:
                insight = insight_future.get_result()
                if insight:
                    template_values[insight.name] = insight
                            
            path = os.path.join(os.path.dirname(__file__), '../templates/insights.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 60 * 60 * 24) 
        
        self.response.out.write(html)

class InsightsDetail(BaseHandler):
    """
    Show Insights for a particular year
    """
    def get(self, year):
        if not year.isdigit():
            return self.redirect("/error/404")
        year = int(year)
        if year not in VALID_YEARS:
            return self.redirect("/error/404")
        
        memcache_key = "insights_detail_%s" % year
        html = memcache.get(memcache_key)
        
        if html is None:
            template_values = {
                'valid_years': VALID_YEARS,
                'selected_year': year,
            }
            
            insight_futures = [Insight.get_by_id_async(Insight.renderKeyName(year, insight_name)) for insight_name in Insight.INSIGHT_NAMES.values()]
            for insight_future in insight_futures:
                insight = insight_future.get_result()
                if insight:
                    template_values[insight.name] = insight
            
            path = os.path.join(os.path.dirname(__file__), '../templates/insights_details.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400) 
        
        self.response.out.write(html)
