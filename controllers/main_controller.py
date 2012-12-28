import os
import logging
import datetime
import time

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

import tba_config

from base_controller import BaseHandler, CacheableHandler

from models.event import Event
from models.team import Team
from models.sitevar import Sitevar

def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)
    
    if html is None:
        path = os.path.join(os.path.dirname(__file__), "../templates/%s.html" % page)
        html = template.render(path, {})
        if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
    
    return html

class MainHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_index"
        self._cache_version = 1

    def _render(self, *args, **kw):
        next_events = Event.query(Event.start_date >= (datetime.datetime.today()  - datetime.timedelta(days=4)))
        next_events.order(Event.start_date).fetch(20)
        
        upcoming_events = []
        for event in next_events:
            if event.start_date.date() < datetime.date.today() + datetime.timedelta(days=4):
                upcoming_events.append(event)
        # Only show events that are happening "the same week" as the first one
        if len(upcoming_events) > 0:
            first_start_date = upcoming_events[0].start_date            
            upcoming_events = [e for e in upcoming_events if ((e.start_date - datetime.timedelta(days=6)) < first_start_date)]
            kickoff_countdown = False
        else:
            kickoff_countdown = True

        template_values = {
            "kickoff_countdown": kickoff_countdown,
            "events": upcoming_events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
        return template.render(path, template_values)

class ContactHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_contact"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/contact.html")
        return template.render(path, {})

class HashtagsHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_hashtags"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/hashtags.html")
        return template.render(path, {})
        
class AboutHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_about"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/about.html")
        return template.render(path, {})

class ThanksHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_thanks"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/thanks.html")
        return template.render(path, {})

class OprHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_opr"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/opr.html")
        return template.render(path, {})

class SearchHandler(BaseHandler):
    def get(self):
        try:
            q = self.request.get("q")
            logging.info("search query: %s" % q)
            if q.isdigit():
                team_id = "frc%s" % q
                team = Team.get_by_id(team_id)
                if team:
                    self.redirect(team.details_url)
                    return None
        except Exception, e:
            logging.warning("warning: %s" % e)
        finally:
            self.response.out.write(render_static("search"))
            
class KickoffHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_kickoff"
        self._cache_version = 2

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/kickoff.html")
        return template.render(path, {})

class GamedayHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_gameday"
        self._cache_version = 1

    def _render(self, *args, **kw):
        next_events = Event.query(Event.start_date >= (datetime.datetime.today() - datetime.timedelta(days=4)))
        next_events.order(Event.start_date).fetch(20)
        
        special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
        special_webcasts_temp = special_webcasts_future.get_result()
        if special_webcasts_temp:
            special_webcasts_temp = special_webcasts_temp.contents
        else:
            special_webcasts_temp = {}
        special_webcasts =  []
        for webcast in special_webcasts_temp.values():
            toAppend = {}
            for key, value in webcast.items():
                toAppend[str(key)] = str(value)
            special_webcasts.append(toAppend)

        ongoing_events = []
        ongoing_events_w_webcasts = []
        for event in next_events:
            if event.start_date.date() < datetime.date.today() + datetime.timedelta(days=4):
                ongoing_events.append(event)
                if event.webcast:
                    valid = []
                    for webcast in event.webcast:
                        if 'type' in webcast and 'channel' in webcast:
                            event_webcast = {'event': event}
                            valid.append(event_webcast)
                    # Add webcast numbers if more than one for an event
                    if len(valid) > 1:
                        count = 1
                        for event in valid:
                            event['count'] = count
                            count += 1
                    ongoing_events_w_webcasts += valid
        
        template_values = {'special_webcasts': special_webcasts,
                           'ongoing_events': ongoing_events,
                           'ongoing_events_w_webcasts': ongoing_events_w_webcasts}
        
        path = os.path.join(os.path.dirname(__file__), '../templates/gameday.html')
        return template.render(path, template_values)

class ChannelHandler(BaseHandler):
    # This is required for the FB JSSDK
    def get(self):
        expires = 60*60*24*365
        self.response.headers.add_header("Pragma", "public")
        self.response.headers.add_header("Cache-Control", "max-age="+str(expires))
        expires_date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(expires + time.time()))
        self.response.headers.add_header("Expires", expires_date)
        self.response.out.write('<script src="//connect.facebook.net/en_US/all.js"></script>')

class PageNotFoundHandler(BaseHandler):
    def get(self):
        self.error(404)
        self.response.out.write(render_static("404"))

class WebcastsHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_webcasts"
        self._cache_version = 1

    def _render(self, *args, **kw):
        events = Event.query(Event.year == 2010).order(Event.start_date).fetch(500)

        template_values = {
            'events': events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/webcasts.html')
        return template.render(path, template_values)
