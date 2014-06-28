import os

from google.appengine.ext.webapp import template

from base_controller import CacheableHandler

from helpers.event_helper import EventHelper


class Gameday2Controller(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "main_gameday2"

    def __init__(self, *args, **kw):
        super(Gameday2Controller, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        events = EventHelper.getWeekEvents()

        webcasts = []
        for event in events:
            webcasts.append({
                "key": event.key_name,
                "name": event.name,
                "webcast": event.webcast,
                })

        self.template_values.update({
            'webcasts': webcasts
        })

        path = os.path.join(os.path.dirname(__file__), '../templates/gameday2.html')
        return template.render(path, self.template_values)
