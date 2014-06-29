import os

from google.appengine.ext.webapp import template

from helpers.event_helper import EventHelper
from models.sitevar import Sitevar

from base_controller import CacheableHandler

from helpers.event_helper import EventHelper


class Gameday2Controller(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_gameday2"

    def __init__(self, *args, **kw):
        super(Gameday2Controller, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

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
                "webcast": event.webcast
            })

        self.template_values.update({
            'events_with_webcasts': events_with_webcasts_dict_list
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday2.html')
        return template.render(path, self.template_values)
