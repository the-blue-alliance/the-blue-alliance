import os

from google.appengine.ext.webapp import template

from helpers.event_helper import EventHelper
from models.sitevar import Sitevar

from base_controller import CacheableHandler

class Gameday2Controller(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_gameday2"
        self._cache_version = 1

    def _render(self, *args, **kw):
        template_values = {}

        events_with_webcasts = []
        for event in EventHelper.getWeekEvents():
            if event.within_a_day and event.webcast:
                events_with_webcasts.append(event)

        events_with_webcasts_dict_list = []
        for event in events_with_webcasts:
            events_with_webcasts_dict_list.append({
                "event_name": event.name,
                "event_key": event.key_name,
                "webcasts": event.webcast
            })

        template_values = {
            'events_with_webcasts': events_with_webcasts_dict_list
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday2.html')
        return template.render(path, template_values)
