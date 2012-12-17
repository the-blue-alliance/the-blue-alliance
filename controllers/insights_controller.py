import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.team_helper import TeamHelper
from helpers.event_helper import EventHelper
from helpers.insights_helper import InsightsHelper

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team
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
            
            for insight_name in InsightsHelper.INSIGHT_NAMES.values():
                insight_key = Insight.renderKeyName(None, insight_name)
                insight = Insight.get_by_id_async(insight_key).get_result()
                if insight:
                    template_values[insight_name] = {'data': insight.data,
                                                     'data_json': insight.data_json}
                            
            path = os.path.join(os.path.dirname(__file__), '../templates/insights.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400) 
        
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
            
            for insight_name in InsightsHelper.INSIGHT_NAMES.values():
                insight_key = Insight.renderKeyName(year, insight_name)
                insight = Insight.get_by_id_async(insight_key).get_result()
                if insight:
                    template_values[insight_name] = {'data': insight.data,
                                                     'data_json': insight.data_json}
            
            path = os.path.join(os.path.dirname(__file__), '../templates/insights_details.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400) 
        
        self.response.out.write(html)
